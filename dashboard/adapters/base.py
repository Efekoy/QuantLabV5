from abc import ABC, abstractmethod


class LabAdapter(ABC):
    """Read-only bridge from a research lab to the dashboard model."""

    @abstractmethod
    def get_lab_metadata(self): ...

    @abstractmethod
    def get_run_status(self): ...

    @abstractmethod
    def get_strategies(self): ...

    @abstractmethod
    def get_stage_results(self, candidate_id): ...

    @abstractmethod
    def get_equity_curves(self, candidate_id): ...

    @abstractmethod
    def get_relationships(self, candidate_id): ...

    @abstractmethod
    def get_protocol_state(self): ...
