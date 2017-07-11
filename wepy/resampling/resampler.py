from wepy.walker import merge
import math
import numpy as np

class Resampler(object):

    def resample(self, walkers, decisions):
        raise NotImplementedError

class NoResampler(Resampler):

    def resample(self, walkers):
        return walkers, None

class WExploreResampler(Resampler):
    pass

class WExplore2Resampler(Resampler):
    # I lied Nazanin put your code here!!
    def __init__(self,nwalk):
        self.ref = md.load('seh_tppu_mdtraj.pdb')
        self.ref = self.ref.remove_solvent()
        self.lig_idx = self.ref.topology.select('resname "2RV"')
        self.b_selection = md.compute_neighbors(self.ref, 0.8, self.lig_idx)
        self.b_selection = np.delete(self.b_selection, self.lig_idx)
        self.n_walkers = None
        self.walkerwt = None
        self.walkers = None
        self.copy_struct = [ i for i in range(self.nwalk) ]
        self.amp =[ 1 for i in range(self.n_walkers)]
        self.distancearray = np.zeros((self.n_walkers, self.n_walkers))

    def __rmsd(self,traj,ref, idx):
        return np.sqrt(3*np.sum(np.square(traj.xyz[:,idx,:] - ref.xyz[:,idx,:]),
                                axis=(1, 2))/idx.shape[0])


    def __MakeTraj (self,Positions):

        Newxyz = np.zeros((1,self.ref.n_atoms, 3))
        for i in range(len(Positions)):
            Newxyz[0,i,:] = ([Positions[i]._value[0],Positions[i]._value[1],
                                                        Positions[i]._value[2]])


        return md.Trajectory(Newxyz,self.ref.topology)

    def CalculateRmsd(self,ind1,ind2):
        positions1 = self.walkers[ind1][0:self.ref.n_atoms]
        positions2 = self.walkers[ind2][0:self.ref.n_atoms]
        ref_traj = self.__MakeTraj(positions1)
        traj = self.__MakeTraj(positions2)
        traj=traj.superpose(ref_traj, atom_indices = self.b_selection)
        return self.__rmsd(traj,ref_traj,self.lig_idx)

    def MakeDistanceArray(self,):
        for i in range(self.n_walkers):
            for j in range (i+1, self.n_walkers):
                self.distancearray[i][j] = self.CalculateRmsd(i, j)


    def __calcspread(self, lpmin, dpower):
        spread = 0
        wsum = np.zeros(self.n_walkers)
        wtfac = np.zeros(self.n_walkers)
        for i in range(self.n_walkers):
            if self.walkerwt[i] > 0 and self.amp[i] > 0:
                wtfac[i] = math.log(self.walkerwt[i]/self.amp[i]) - lpmin
            else:
                wtfac[i] = 0
            if wtfac[i] < 0:
                wtfac[i] = 0

        for i in range(self.n_walkers-1):
            if self.amp[i] > 0:
                for j in range(i+1,self.n_walkers):
                    if self.amp[j] > 0:
                        d = self.distancearray[i][j] ** dpower * wtfac[i]*wtfac[j];
                        spread += d * self.amp[i] * self.amp[j];
                        wsum[i] += d * self.amp[j];
                        wsum[j] += d * self.amp[i];

        return(spread,wsum)

    def __merge(self, i, j):
        self.walkerwt[j] += self.walkerwt[i]
        self.walkerwt[i] = 0
        self.amp[i] = 0
        self.amp[j] = 1


    def __copystructure(self, a, b):
        # this function will copy the simulation details from walker a to walker b
        self.copy_struct[a] = b

    def decide(self,):
        pmin = 1e-12
        pmax = 0.1
        lpmin = math.log(pmin/100)
        dpower = 4
        productive = True
        mergedist = 0.25
        spread, wsum = self.__calcspread(lpmin, dpower)
        print("Starting variance:", spread)
        while productive :
            productive = False
            # find min and max wsums, alter @self.amp
            minwsum = 1.0
            maxwsum = 0.0
            minwind = None
            maxwind = None
            for i in range(0, self.n_walkers-1):
                # determine eligibility and find highest wsum (to clone) and lowest wsum (to merge)
                if self.amp[i] >= 1 or self.walkerwt[i] > pmin:  # find the most clonable walker
                    if wsum[i] > maxwsum:
                        maxwsum = wsum[i]
                        maxwind = i
                if self.amp[i] == 1 or  self.walkerwt[i] < pmax:  # find the most mergeable walker
                    if wsum[i] < minwsum: # convert or to and  (important)
                        minwsum = wsum[i]
                        minwind = i

            # does minwind have an eligible merging partner?
            closedist = mergedist
            closewalk = None
            if minwind is not None and maxwind is not None and minwind != maxwind:
                for j in range(0, self.n_walkers):
                    if j != minwind and j != maxwind:
                        if self.distancearray[minwind][j]<closedist and self.amp[j] == 1 and self.walkerwt[j]<pmax :
                            closedist = self.distancearray[minwind][j]
                            closewalk = j
        # did we find a closewalk?
            if minwind is not None and maxwind is not None and closewalk is not None:
                if self.amp[minwind] != 1:
                    die("Error! minwind", minwind, "has self.amp =",self.amp[minwind])
                if self.amp[closewalk] != 1:
                    die("Error! closewalk", closewalk, "has self.amp=",self.amp[closewalk])


                # change self.amp
                tempsum = self.walkerwt[minwind] + self.walkerwt[closewalk]
                self.amp[minwind] = self.walkerwt[minwind]/tempsum
                self.amp[closewalk] = self.walkerwt[closewalk]/tempsum
                self.amp[maxwind] += 1

                # re-determine spread function, and wsum values
                (newspread, wsum) = self.__calcspread(lpmin ,dpower)

                if newspread > spread:
                    print("Variance move to",newspread,"accepted")
                    productive = True
                    spread = newspread

                    # make a decision on which walker to keep (minwind, or closewalk)
                    r = np.random.random(self.walkerwt[closewalk] + self.walkerwt[minwind])
                    if r < self.walkerwt[closewalk]:
                        # keep closewalk, get rid of minwind
                        self.__merge(minwind,closewalk)
                    else:
                        # keep minwind, get rid of closewalk
                        self.__merge(closewalk, minwind)

                    (newspread, wsum) = self.__calcspread(lpmin ,dpower)
                    print("variance after selection:",newspread);

                else: # Not productive
                    self.amp[minwind] = 1
                    self.amp[closewalk] = 1
                    self.amp[maxwind] -= 1

        # end of while productive loop:  done with cloning and merging steps
        # set walkerdist arrays
        walkerdist = wsum

        # Perform the cloning and merging steps
        # start with an empty free walker array, add all walkers with amp = 0
        freewalkers =[]
        for r1walk in range(0,self.n_walkers):
            if self.amp[r1walk] == 0 :
                freewalkers.append(r1walk)

        # for each self.amp[i] > 1, clone!
        for r1walk in range(0,self.n_walkers):
            if self.amp[r1walk] > 1:
                nclone = self.amp[r1walk]-1
                inds = []
                for i in range(0,nclone):
                    try:
                        tind = freewalkers.pop()
                    except:
                        raise("Error! Not enough free walkers!")
                    if r1walk == tind:
                        raise("Error!  free walker is equal to the clone!")
                    else:
                        inds.append(tind )

                newwt=self.walkerwt[r1walk]/(nclone+1)
                self.walkerwt[r1walk] = newwt
                for tind in inds:
                    self.walkerwt[tind]= newwt
                    walkerdist[tind]=walkerdist[r1walk]
                    self.__copystructure(r1walk,tind)
                    # done cloning and meging
            if len(freewalkers) > 0:
                raise("Error! walkers left over after merging and cloning")



    def resample(self, walkers):
        self.walkers = walkers
        self.n_walkers = len(self.walkers)
        self.walkerwt = [ walker.weight for walker in self.walkers ]
        self.MakeDistanceArray()
        self.decide()
        for i in range(self.n_walkers):
                item = walker()
                item.Walker_ID = i
                # determine  parent
                if self.copy_struct[i] != i:
                    item.restartpoint = self.walkers[self.copy_struct[i]].restartpoint
                    item.parent_ID = self.copy_struct[i]
                else:
                    item.restartpoint = self.walkers[i].restartpoint
                    item.parent_ID = i
                item.weight = self.walkerwt[i]
                self.walkers[i] = item

        return self.walkers, None
