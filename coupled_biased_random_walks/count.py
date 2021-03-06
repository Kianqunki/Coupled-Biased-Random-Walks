from collections import Counter, defaultdict
from itertools import combinations, tee

from six import iteritems

try:
    # python 2
    from collections import Mapping
except ImportError:
    # python 3
    from collections.abc import Mapping


def get_feature_name(feature_tuple):
    """
    Helper function to return feature name from tuple representation
    :param feature_tuple: tuple of the form (feature_name, feature_value)
    """
    return feature_tuple[0]


def get_mode(counter):
    """
    Helper function to return the most common element from a counter
    :param counter: collections.Counter instance
    """
    return counter.most_common(1)[0][1]


class IncrementingDict(Mapping):

    """
    Dict-like class for assigning an incrementing value to new keys and
    does not allow overwriting of a key.
    Inherits abstract base class Mapping instead of dict; note that we
    intentionally do not define a __setitem__ method
    """

    def __init__(self):
        self._d = {}
        self._next_val = 0

    def insert(self, key):
        """
        Inserts a (strictly new) key
        :param key: any hashable object to be used as a key
        """
        if key in self._d:
            return
        self._d[key] = self._next_val
        self._next_val += 1

    def __getitem__(self, key):
        return self._d[key]

    def __iter__(self):
        return self._d.__iter__()

    def __len__(self):
        return self._d.__len__()

    def __repr__(self):
        return self._d.__repr__()


class ObservationCounter(object):

    """
    Counts single and joint occurrences of key/value pairs in a dict with
    the intention that an observation of categorical features is represented
    as a dict of {feature_name: categorical_level/feature_value, ...}
    """

    def __init__(self):
        # total number of observations counted
        self.n_obs = 0
        # stores individual counts of features, keyed by feature name and then
        # by (feature_name, feature_value) tuple
        self._counts = defaultdict(Counter)
        # stores joint counts of features, keyed by (feature_tuple1, feature_tuple2)
        # where each feature tuple takes the form (feature_name, feature_value)
        self._joint_counts = Counter()
        # maps each feature tuple to a (unique, incrementing integer) index
        self._index = IncrementingDict()

    @property
    def counts(self):
        return dict(self._counts)

    @property
    def joint_counts(self):
        return dict(self._joint_counts)

    @property
    def index(self):
        return self._index

    def update(self, observation_iterable):
        """
        Update counts with new observation(s)
        :param observation_iterable: list of dicts
        """
        if isinstance(observation_iterable, dict):
            observation_iterable = [observation_iterable]
        for observation in observation_iterable:
            # create 3 iterators
            obs1, obs2, obs3 = tee(iteritems(observation), 3)
            self._update_counts(obs1)
            self._update_joint_counts(obs2)
            self._update_index(obs3)
            # In the future we might need to track n_obs per feature
            # and store it in a dict; this might require skipping features
            # with value nan.  For now just count each observation.
            self.n_obs += 1

    def _update_counts(self, observation):
        """
        Update single counts
        :param observation: list of tuples of the form ('feature_name', 'feature_value')
        """
        for item in observation:
            feature_name = get_feature_name(item)
            self._counts[feature_name].update([item])

    def _update_joint_counts(self, observation):
        """
        Update joint counts
        :param observation: list of tuples of the form ('feature_name', 'feature_value')
        """
        pairs = combinations(sorted(observation), 2)
        self._joint_counts.update(pairs)

    def _update_index(self, observation):
        """
        Update index mapping
        :param observation: list of tuples of the form ('feature_name', 'feature_value')
        """
        for item in observation:
            self._index.insert(item)

    def get_count(self, item):
        """
        Getter to safely retrieve count from interal data structure of defaultdict(Counter)
        :param item: tuple of the form ('feature_name', 'feature_value')
        """
        feature_name = get_feature_name(item)
        try:
            return self._counts.get(feature_name)[item]
        except TypeError:
            # feature_name is not in self._counts
            return 0
