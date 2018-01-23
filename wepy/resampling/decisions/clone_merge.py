from collections import namedtuple, defaultdict
from enum import Enum
from string import ascii_lowercase

import numpy as np

from wepy.resampling.decisions.decision import Decision

from wepy.walker import split, keep_merge


class CloneMergeDecision(Decision):

    # the possible types of decisions that can be made enumerated for
    # storage, these each correspond to specific instruction type
    class CloneMergeDecisionEnum(Enum):
        NOTHING = 1
        CLONE = 2
        SQUASH = 3
        KEEP_MERGE = 4

    ENUM = CloneMergeDecisionEnum

    # namedtuple records for each decision type
    INSTRUCTION_RECORDS = (
        (ENUM.NOTHING, namedtuple("NothingInstructionRecord", ['slot'])),
        (ENUM.CLONE, namedtuple("CloneInstructionRecord", ['slot_a', 'slot_b'])),
        (ENUM.SQUASH, namedtuple("SquashInstructionRecord", ['merge_slot'])),
        (ENUM.KEEP_MERGE, namedtuple("KeepMergeInstructionRecord", ['slot'])),
    )

    # datatypes for each instruction, useful for allocating memory in
    # databases. Datatypes may be converted to a numpy dtype by
    # calling `dtype(instruct_dtype)`
    INSTRUCTION_DTYPES = (
        (ENUM.NOTHING, [('pos', np.int)]),
        (ENUM.CLONE, [('slot_a', np.int), ('slot_b', np.int)]),
        (ENUM.SQUASH, [('merge_to', np.int)]),
        (ENUM.KEEP_MERGE, [('pos', np.int)]),
    )

    @classmethod
    def action(cls, walkers, decisions):
        """Performs cloning and merging according to a list of resampling
        records for some walkers."""

        # list for the modified walkers
        mod_walkers = [None for i in range(len(walkers))]

        # we need to collect groups of merges, one entry for each
        # merge, where the key is the walker_idx of the keep merge slot
        squash_walkers = defaultdict(list)
        keep_walkers = {}
        # go through each decision and perform the decision
        # instructions
        for walker_idx, decision in enumerate(decisions):
            decision_value, instruction = decision

            if decision_value == cls.ENUM.NOTHING.value:
                # check to make sure a walker doesn't already exist
                # where you are going to put it
                if mod_walkers[instruction[0]] is not None:
                    raise ValueError(
                        "Multiple walkers assigned to position {}".format(instruction[0]))

                # put the walker in the position specified by the
                # instruction
                mod_walkers[instruction[0]] = walkers[walker_idx]

            elif decision_value == cls.ENUM.CLONE.value:
                walker = walkers[walker_idx]
                clones = split(walker, number=len(instruction))

                for i, walker_idx in enumerate(instruction):
                    if mod_walkers[walker_idx] is not None:
                        raise ValueError(
                            "Multiple walkers assigned to position {}".format(instruction[0]))
                    mod_walkers[walker_idx] = clones[i]

            # if it is a decision for merging we must perform this
            # once we know all the merge targets for each merge group
            elif decision_value == cls.ENUM.SQUASH.value:

                # save this walker to the appropriate merge group to
                # merge after going through the list of walkers
                squash_walkers[instruction[0]].append(walker_idx)

            elif decision_value == cls.ENUM.KEEP_MERGE.value:
                keep_walkers[instruction[0]] = walker_idx

            else:
                raise ValueError("Decision not recognized")

        # do the merging for each merge group
        for target_idx, walker_idxs in squash_walkers.items():
            keep_idx = keep_walkers[target_idx]
            # collect the walkers in the merge group, the keep idx is
            # always the first in the list
            merge_grp = [walkers[keep_idx]] + [walkers[i] for i in walker_idxs]

            # merge the walkers
            merged_walker = keep_merge(merge_grp, 0)

            # make sure there is not already a walker in this slot
            if mod_walkers[target_idx] is not None:
                raise ValueError(
                    "Multiple walkers assigned to position {}".format(target_idx))

            # set it in the slot for the keep_idx
            mod_walkers[target_idx] = merged_walker

        return mod_walkers

def alphabet_iterator():
    num_chars = 1
    alphabet_it = iter(ascii_lowercase)
    while True:
        try:
            letter = next(alphabet_it)
        except StopIteration:
            alphabet_it = iter(ascii_lowercase)
            letter = next(alphabet_it)
            num_chars += 1

        yield letter * num_chars

class VariableLengthRecord(object):
    def __init__(self, name, *values):
        self._fields = ()
        self._data = values
        self._name = name

        key_it = alphabet_iterator()
        # add them to the object namespace alphanumerically
        for value in values:
            key = next(key_it)
            self.__dict__[key] = value
            self._fields += (key,)

    def __getitem__(self, idx):
        return self._data[idx]

    def __str__(self):
        return "{}({})".format(self._name,
                    ', '.join(["{}={}".format(key, self.__dict__[key]) for key in self._fields]))

class MultiCloneMergeDecision(Decision):

    # the possible types of decisions that can be made enumerated for
    # storage, these each correspond to specific instruction type
    class CloneMergeDecisionEnum(Enum):
        NOTHING = 1
        CLONE = 2
        SQUASH = 3
        KEEP_MERGE = 4

    ENUM = CloneMergeDecisionEnum

    # namedtuple records for each decision type
    INSTRUCTION_RECORDS = (
        (ENUM.NOTHING, namedtuple("NothingInstructionRecord", ['slot'])),
        (ENUM.CLONE, namedtuple("CloneInstructionRecord", Ellipsis)),
        (ENUM.CLONE, namedtuple("CloneInstructionRecord", ['slot_a', 'slot_b'])),
        (ENUM.SQUASH, namedtuple("SquashInstructionRecord", ['merge_slot'])),
        (ENUM.KEEP_MERGE, namedtuple("KeepMergeInstructionRecord", ['slot'])),
    )

    # datatypes for each instruction, useful for allocating memory in
    # databases. Datatypes may be converted to a numpy dtype by
    # calling `dtype(instruct_dtype)`
    INSTRUCTION_DTYPES = (
        (ENUM.NOTHING, [('pos', np.int)]),
        (ENUM.CLONE, [('slot_a', np.int), ('slot_b', np.int)]),
        (ENUM.SQUASH, [('merge_to', np.int)]),
        (ENUM.KEEP_MERGE, [('pos', np.int)]),
    )

    @classmethod
    def action(cls, walkers, decisions):
        """Performs cloning and merging according to a list of resampling
        records for some walkers."""

        # list for the modified walkers
        mod_walkers = [None for i in range(len(walkers))]

        # we need to collect groups of merges, one entry for each
        # merge, where the key is the walker_idx of the keep merge slot
        squash_walkers = defaultdict(list)
        keep_walkers = {}
        # go through each decision and perform the decision
        # instructions
        for walker_idx, decision in enumerate(decisions):
            decision_value, instruction = decision

            if decision_value == cls.ENUM.NOTHING.value:
                # check to make sure a walker doesn't already exist
                # where you are going to put it
                if mod_walkers[instruction[0]] is not None:
                    raise ValueError(
                        "Multiple walkers assigned to position {}".format(instruction[0]))

                # put the walker in the position specified by the
                # instruction
                mod_walkers[instruction[0]] = walkers[walker_idx]

            elif decision_value == cls.ENUM.CLONE.value:
                walker = walkers[walker_idx]
                clones = split(walker, number=len(instruction))

                for i, walker_idx in enumerate(instruction):
                    if mod_walkers[walker_idx] is not None:
                        raise ValueError(
                            "Multiple walkers assigned to position {}".format(instruction[0]))
                    mod_walkers[walker_idx] = clones[i]

            # if it is a decision for merging we must perform this
            # once we know all the merge targets for each merge group
            elif decision_value == cls.ENUM.SQUASH.value:

                # save this walker to the appropriate merge group to
                # merge after going through the list of walkers
                squash_walkers[instruction[0]].append(walker_idx)

            elif decision_value == cls.ENUM.KEEP_MERGE.value:
                keep_walkers[instruction[0]] = walker_idx

            else:
                raise ValueError("Decision not recognized")

        # do the merging for each merge group
        for target_idx, walker_idxs in squash_walkers.items():
            keep_idx = keep_walkers[target_idx]
            # collect the walkers in the merge group, the keep idx is
            # always the first in the list
            merge_grp = [walkers[keep_idx]] + [walkers[i] for i in walker_idxs]

            # merge the walkers
            merged_walker = keep_merge(merge_grp, 0)

            # make sure there is not already a walker in this slot
            if mod_walkers[target_idx] is not None:
                raise ValueError(
                    "Multiple walkers assigned to position {}".format(target_idx))

            # set it in the slot for the keep_idx
            mod_walkers[target_idx] = merged_walker

        return mod_walkers
