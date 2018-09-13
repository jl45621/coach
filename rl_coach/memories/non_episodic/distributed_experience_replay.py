#
# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from typing import List, Tuple, Union, Dict, Any

import numpy as np
import redis
import uuid
import pickle

from rl_coach.core_types import Transition
from rl_coach.memories.memory import Memory, MemoryGranularity, MemoryParameters
from rl_coach.utils import ReaderWriterLock


class DistributedExperienceReplayParameters(MemoryParameters):
    def __init__(self):
        super().__init__()
        self.max_size = (MemoryGranularity.Transitions, 1000000)
        self.allow_duplicates_in_batch_sampling = True

    @property
    def path(self):
        return 'rl_coach.memories.non_episodic.distributed_experience_replay:DistributedExperienceReplay'


class DistributedExperienceReplay(Memory):
    """
    A regular replay buffer which stores transition without any additional structure
    """
    def __init__(self, max_size: Tuple[MemoryGranularity, int], allow_duplicates_in_batch_sampling: bool=True, 
                 redis_ip = 'localhost', redis_port = 6379, db = 0):
        """
        :param max_size: the maximum number of transitions or episodes to hold in the memory
        :param allow_duplicates_in_batch_sampling: allow having the same transition multiple times in a batch
        """
        
        super().__init__(max_size)
        if max_size[0] != MemoryGranularity.Transitions:
            raise ValueError("Experience replay size can only be configured in terms of transitions")
        # self.transitions = []
        self.allow_duplicates_in_batch_sampling = allow_duplicates_in_batch_sampling

        self.db = db
        self.redis_connection = redis.Redis(redis_ip, redis_port, self.db)

    def length(self) -> int:
        """
        Get the number of transitions in the ER
        """
        return self.num_transitions()

    def num_transitions(self) -> int:
        """
        Get the number of transitions in the ER
        """
        # Replace with distributed store len
        return self.redis_connection.info(section='keyspace')['db{}'.format(self.db)]['keys']
        # return len(self.transitions)

    def sample(self, size: int) -> List[Transition]:
        """
        Sample a batch of transitions form the replay buffer. If the requested size is larger than the number
        of samples available in the replay buffer then the batch will return empty.
        :param size: the size of the batch to sample
        :param beta: the beta parameter used for importance sampling
        :return: a batch (list) of selected transitions from the replay buffer
        """        
        transition_idx = dict()
        if self.allow_duplicates_in_batch_sampling:
            while len(transition_idx) != size:
                key = self.redis_connection.randomkey()
                transition_idx[key] = pickle.loads(self.redis_connection.get(key))
            # transition_idx = np.random.randint(self.num_transitions(), size=size)

        else:
            if self.num_transitions() >= size:
                while len(transition_idx) != size:
                    key = self.redis_connection.randomkey()
                    if key in transition_idx:
                        continue
                    transition_idx[key] = pickle.loads(self.redis_connection.get(key))
                # transition_idx = np.random.choice(self.num_transitions(), size=size, replace=False)
            else:
                raise ValueError("The replay buffer cannot be sampled since there are not enough transitions yet. "
                                 "There are currently {} transitions".format(self.num_transitions()))

        # Replace with distributed store
        batch = transition_idx.values()

        return batch

    def _enforce_max_length(self) -> None:
        """
        Make sure that the size of the replay buffer does not pass the maximum size allowed.
        If it passes the max size, the oldest transition in the replay buffer will be removed.
        This function does not use locks since it is only called internally
        :return: None
        """
        granularity, size = self.max_size
        if granularity == MemoryGranularity.Transitions:
            while size != 0 and self.num_transitions() > size:
                self.redis_connection.delete(self.redis_connection.randomkey())
        else:
            raise ValueError("The granularity of the replay buffer can only be set in terms of transitions")

    def store(self, transition: Transition, lock: bool=True) -> None:
        """
        Store a new transition in the memory.
        :param transition: a transition to store
        :param lock: if true, will lock the readers writers lock. this can cause a deadlock if an inheriting class
                     locks and then calls store with lock = True
        :return: None
        """
        # Replace with distributed store

        self.redis_connection.set(uuid.uuid4(), pickle.dumps(transition))
        # self.transitions.append(transition)
        self._enforce_max_length()

    def get_transition(self, transition_index: int, lock: bool=True) -> Union[None, Transition]:
        """
        Returns the transition in the given index. If the transition does not exist, returns None instead.
        :param transition_index: the index of the transition to return
        :param lock: use write locking if this is a shared memory
        :return: the corresponding transition
        """
        # Replace with distributed store
        import pytest; pytest.set_trace()
        return pickle.loads(self.redis_connection.get(transition_index))
        
    def remove_transition(self, transition_index: int, lock: bool=True) -> None:
        """
        Remove the transition in the given index.

        This does not remove the transition from the segment trees! it is just used to remove the transition
        from the transitions list
        :param transition_index: the index of the transition to remove
        :return: None
        """
        # Replace with distributed store
        import pytest; pytest.set_trace()
        self.redis_connection.delete(transition_index)
        
    # for API compatibility
    def get(self, transition_index: int, lock: bool=True) -> Union[None, Transition]:
        """
        Returns the transition in the given index. If the transition does not exist, returns None instead.
        :param transition_index: the index of the transition to return
        :return: the corresponding transition
        """
        # Replace with distributed store
        import pytest; pytest.set_trace()
        return self.get_transition(transition_index, lock)

    # for API compatibility
    def remove(self, transition_index: int, lock: bool=True):
        """
        Remove the transition in the given index
        :param transition_index: the index of the transition to remove
        :return: None
        """
        # Replace with distributed store
        import pytest; pytest.set_trace()
        self.remove_transition(transition_index, lock)

    def clean(self, lock: bool=True) -> None:
        """
        Clean the memory by removing all the episodes
        :return: None
        """
        import pytest; pytest.set_trace()
        self.redis_connection.flushall()
        # self.transitions = []

    def mean_reward(self) -> np.ndarray:
        """
        Get the mean reward in the replay buffer
        :return: the mean reward
        """
        # Replace with distributed store
        import pytest; pytest.set_trace()
        mean = np.mean([pickle.loads(self.redis_connection.get(key)).reward for key in self.redis_connection.keys()])
        # mean = np.mean([transition.reward for transition in self.transitions])

        return mean