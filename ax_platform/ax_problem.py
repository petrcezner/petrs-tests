import pytorch_lightning as pl


class AxProblem:
    def __init__(self, data_module: pl.LightningDataModule, fit_function):
        self.dm = data_module
        self.fit_function = fit_function

    def __call__(self, params):
        model, trainer = self.fit_function(dm=self.dm, **params)
        result = trainer.validate()
        return result
