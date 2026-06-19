"""
VideoMind AI — Embedding Model Registry
==========================================
Singleton + Factory that manages all registered embedding models.

DESIGN PATTERN — Singleton:
    ModelRegistry is instantiated once per process. Loading a 384-dim
    sentence-transformer model is expensive (~200ms); this ensures it
    happens once and the loaded model is reused across all requests.

DESIGN PATTERN — Factory:
    get_model(name) encapsulates all construction logic. Callers never
    call model constructors directly.

SOLID — Open/Closed:
    New embedding models are added by registering them in _REGISTRY.
    The EmbeddingService and all callers never change.

SOLID — Dependency Inversion:
    All returned models implement IEmbeddingModel. Callers depend on
    the interface, not on BGEModel or any concrete class.
"""

from __future__ import annotations

from app.core.exceptions import EmbeddingModelNotFoundError
from app.domain.interfaces import IEmbeddingModel

# Stub — implementation in Phase 6

# Registry maps model name strings → IEmbeddingModel factory callables
_REGISTRY: dict[str, type] = {}

_instance: "ModelRegistry | None" = None


class ModelRegistry:
    """
    Singleton registry that lazily instantiates and caches embedding models.
    """

    _loaded_models: dict[str, IEmbeddingModel] = {}

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        """
        Return the singleton ModelRegistry instance.

        DESIGN PATTERN — Singleton:
            Only one registry exists per process. This is safe because
            model loading is idempotent and models are stateless at inference.
        """
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance

    def get_model(self, model_name: str) -> IEmbeddingModel:
        """
        Return a cached IEmbeddingModel, loading it on first access.

        DESIGN PATTERN — Factory:
            Construction details (path, device, batch size) are hidden here.
            Callers only need the model name string.

        Args:
            model_name: Registered model identifier (e.g., "BAAI/bge-small-en-v1.5").

        Returns:
            An IEmbeddingModel ready for inference.

        Raises:
            EmbeddingModelNotFoundError: If model_name is not in the registry.
        """
        # Return cached model if already loaded
        if model_name in self._loaded_models:
            return self._loaded_models[model_name]

        model_factory = _REGISTRY.get(model_name)
        if model_factory is None:
            raise EmbeddingModelNotFoundError(model_name)

        # Instantiate model: factory may be a class or callable returning an instance
        model = model_factory() if callable(model_factory) else model_factory

        # Validate interface
        if not isinstance(model, IEmbeddingModel):
            raise TypeError(f"Registered model '{model_name}' does not implement IEmbeddingModel")

        self._loaded_models[model_name] = model
        return model


    @classmethod
    def register(cls, name: str, model_class: type) -> None:
        """
        Register a new IEmbeddingModel class under a given name.

        SOLID — Open/Closed:
            Called once per new model class at import time. No existing
            code is modified.

        Args:
            name: The model identifier string.
            model_class: A class implementing IEmbeddingModel.
        """
        _REGISTRY[name] = model_class
