import hydra
import omegaconf
import pytorch_lightning as pl


class AxProblem:
    def __init__(self, data_module: pl.LightningDataModule, fit_function: omegaconf.DictConfig, repetition: int = 2):
        self.dm = data_module
        self.fit_function = fit_function
        self.repetition = repetition

    def __call__(self, params):
        model, trainer, result = hydra.utils.instantiate(self.fit_function, dm=self.dm, **params)
        return {r: (result[0][r], 0.0) for r in result[0]}
