"""Natural frequency distribution registry for Kuramoto oscillators."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
import numpy as np


class DistributionRegistry:
    """Extensible registry for oscillator natural frequency distributions."""

    _distributions: Dict[str, Callable[..., np.ndarray]] = {}
    _descriptions: Dict[str, str] = {}

    @classmethod
    def register(
        cls,
        name: str,
        dist_fn: Callable[..., np.ndarray],
        description: str = "",
    ) -> None:
        """Register a frequency distribution sampler."""
        cls._distributions[name] = dist_fn
        cls._descriptions[name] = description

    @classmethod
    def get_available(cls) -> List[Dict[str, str]]:
        """Return list of available frequency distributions for UI dropdowns."""
        return [
            {"label": desc or key.title(), "value": key}
            for key, desc in cls._descriptions.items()
        ]

    @classmethod
    def sample(
        cls,
        name: str,
        n: int,
        seed: Optional[int] = None,
        custom_values: Optional[List[float]] = None,
        **kwargs: Any,
    ) -> np.ndarray:
        """Sample natural frequencies according to specified distribution."""
        name_key = name.lower()
        if name_key not in cls._distributions:
            name_key = "normal"

        dist_fn = cls._distributions.get(name_key, cls._sample_normal)
        return dist_fn(n=n, seed=seed, custom_values=custom_values, **kwargs)

    @staticmethod
    def _sample_normal(n: int, mean: float = 0.0, std: float = 1.0, seed: Optional[int] = None, **kwargs: Any) -> np.ndarray:
        rng = np.random.default_rng(seed)
        return rng.normal(loc=mean, scale=std, size=n)

    @staticmethod
    def _sample_uniform(n: int, low: float = -1.0, high: float = 1.0, seed: Optional[int] = None, **kwargs: Any) -> np.ndarray:
        rng = np.random.default_rng(seed)
        return rng.uniform(low=low, high=high, size=n)

    @staticmethod
    def _sample_bimodal(n: int, mean1: float = -1.0, mean2: float = 1.0, std: float = 0.3, seed: Optional[int] = None, **kwargs: Any) -> np.ndarray:
        rng = np.random.default_rng(seed)
        n1 = n // 2
        n2 = n - n1
        samples = np.concatenate([
            rng.normal(loc=mean1, scale=std, size=n1),
            rng.normal(loc=mean2, scale=std, size=n2),
        ])
        rng.shuffle(samples)
        return samples

    @staticmethod
    def _sample_golden_ratio(n: int, base: float = 1.0, seed: Optional[int] = None, **kwargs: Any) -> np.ndarray:
        phi = (1 + np.sqrt(5)) / 2
        # Deterministic golden ratio sequence centered around 0
        indices = np.arange(1, n + 1)
        samples = (indices * phi) % 1.0
        return (samples - 0.5) * base * 2.0

    @staticmethod
    def _sample_custom(n: int, custom_values: Optional[List[float]] = None, seed: Optional[int] = None, **kwargs: Any) -> np.ndarray:
        if custom_values is not None and len(custom_values) > 0:
            arr = np.array(custom_values, dtype=float)
            if len(arr) == n:
                return arr
            if len(arr) > n:
                return arr[:n]
            # Repeat to match n
            repeats = int(np.ceil(n / len(arr)))
            return np.tile(arr, repeats)[:n]
        return DistributionRegistry._sample_normal(n=n, seed=seed)


# Register standard distributions
DistributionRegistry.register("normal", DistributionRegistry._sample_normal, "Normal (Gaussian)")
DistributionRegistry.register("uniform", DistributionRegistry._sample_uniform, "Uniform [-1, 1]")
DistributionRegistry.register("bimodal", DistributionRegistry._sample_bimodal, "Bimodal")
DistributionRegistry.register("golden_ratio", DistributionRegistry._sample_golden_ratio, "Golden Ratio")
DistributionRegistry.register("custom", DistributionRegistry._sample_custom, "Custom List")
