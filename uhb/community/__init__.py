"""Community dataset — crowd-sourced benchmark data for continuous improvement.

Users contribute benchmark runs to build a global map of
model × harness × environment × task performance.
"""

from .schema import CommunityRun, CommunityDataset
from .leaderboard import Leaderboard

__version__ = "0.1.0"
__all__ = ["CommunityRun", "CommunityDataset", "Leaderboard"]
