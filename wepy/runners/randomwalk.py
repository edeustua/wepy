import random as rand

import numpy as np

from simtk import unit

from wepy.runners.runner import Runner
from wepy.walker import Walker, WalkerState

UNIT_NAMES = (('positions_unit', unit.nanometer.get_name()),
         ('time_unit', unit.picosecond.get_name()),
        )

class RandomWalkRunner(Runner):
    """RandomWalkRunner is an object for implementing the dynamic of
    RandomWalk system. To use it, you need to provide the number of dimensions
    and the probability of movement.
    """
    def __init__(self, dimension=2, probability=0.25):
        """Initialize RandomWalk object with the number of
        dimension and probability.

        :param dimension: integer

        :param probability: float
        """

        self.dimension = dimension
        self.probability = probability


    def walk(self, positions):
        """Impliment the dynamic of RandomWalk system for one step.
        Takes the current position vector as input and based on the probability
        generates new position for each dimension and returns new posiotion
        vector.
        :param positions: a numpy array of shape (1, dimension)
        :returns: new posiotion
        :rtype:a numpy array of shape (1, dimension)
        """
        # make the deep copy of current posiotion
        new_positions = positions.copy()

        # iterates over each dimension
        for dimension in range(self.dimension):
            # Generates an uniform random number to choose between increasing or decreasing position
            r = rand.uniform(0, 1)

            # make a forward movement
            if r < self.probability:
                new_positions[0][dimension] += 1
            # make a backward movement
            else:
                new_positions[0][dimension] -= 1

            # implement the boundary condition for movement, movements to -1 are rejected
            if new_positions [0][dimension] < 0:
                new_positions[0][dimension] = 0

        return new_positions

    def run_segment(self, walker, segment_length):
        """Run dynamics of RandomWalk system for the number of steps
        that is specified by segment_length.

        :param walker: a RandomWalk object
        :param segment_length: the number of steps
        :returns: a RandomWalk object with new positions
        :rtype:
        """
        # Gets the current posiotion of RandomWalk Walker
        positions = walker.positions
        # Make movements for the segment_length steps
        for segment_idx in range(segment_length):
            # calls walk function for one step movement
            new_positions = self.walk(positions)
            positions = new_positions
        # makes new state form new positions
        new_state = RandomWalkState(new_positions, 0.0)
        # creates new_walker from new state and current weight
        new_walker = RandomWalker(new_state, walker.weight)
        return new_walker


class RandomWalker(Walker):
    """
    RandomWalker is a subtype of walker object and stores the information of
    RandomWalk object.
    """

    def __init__(self, state, weight):
        """Initialize RandomWalker object and creates new walker.
        :param state: state object that has position and time information.
        :param weight: the weight that associated with the walker.
        """

        super().__init__(state, weight)
        self._keys = ['positions', 'time']

    def dict(self):
        """Return a dict of the values."""
        return {'positions' : self.state.getPositions(),
                'time' : self.time,
               }
    def keys(self):
        """Return the keys of the dictionary"""
        return self._keys

    def __getitem__(self, key):
        """Return the value of the key

        :param key: The key
        :returns: The value of the key
        :rtype:

        """
        if key == 'positions':
            return self.state.positions
        elif key == 'time':
            return self.time
        else:
            raise KeyError('{} not an RandomWalker attribute')


    @property
    def positions(self):
        """A property method that returns the current position of the walker.

        :returns: the current posiotion
        :rtype: a numpy array of a shape (1, dimension)

        """

        try:
            return self.state.getPositions()
        except TypeError:
            return None

    @property
    def positions_unit(self):
        """Return the unit of positions"""

        return self.positions.unit

    @property
    def time(self):
        """Return the time"""

        return self.state.getTime()




class RandomWalkState(WalkerState):
    """
    State object stores the information about a RandomWalk object like positions and time.
    """

    def __init__(self, positions, time):
        """Creates a State object and initialize it.

        :param positions: A numpy array of position
        :param time: time
        """

        self.positions = positions.copy()
        self.time = time
        self._data = {'positions' : self.positions,
                      'time' : self.time}

    def __getitem__(self, key):
        return self._data[key]

    def getPositions(self):
        """Return current posiotion of the Walker

        :returns:  posiotion
        :rtype: A numpy array of shape (1, dimension)
        """

        return self.positions

    def getTime(self):
        """Return the time"""
        return self.time