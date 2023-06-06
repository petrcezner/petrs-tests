import logging
from datetime import datetime
from pathlib import Path

from ax.service.ax_client import AxClient
from ax.service.managed_loop import optimize
from ax_problem import AxProblem
from omegaconf import DictConfig, OmegaConf

logger = logging.getLogger(__name__)


class AxHyperparameterSearch:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.evaluate = AxProblem(cfg.data_module, cfg.fit_function)
        self.ax_client = AxClient()

    def __call__(self):
        best_parameters, values, experiment, model = optimize(
            **OmegaConf.to_container(self.cfg.ax), evaluation_function=self.evaluate
        )
        if self.cfg.save_to_file:
            self.save_current_experiment(self.cfg.ax.experiment_name)
        self.save_result(best_parameters, self.cfg.ax.experiment_name)

    def cycle_call(self):
        self.ax_client.create_experiment(**OmegaConf.to_container(self.cfg.ax))
        for i in range(self.cfg.ax.choose_generation_strategy_kwargs.num_initialization_trials):
            parameters, trial_index = self.ax_client.get_next_trial()
            self.ax_client.complete_trial(trial_index=trial_index, raw_data=self.evaluate(parameters))
            if self.cfg.save_to_file:
                self.save_current_experiment(self.cfg.ax.name)
        best_parameters, values = self.ax_client.get_best_parameters()
        self.save_result(best_parameters, self.cfg.ax.name)
        return

    def save_current_experiment(self, experiment_name):
        experiment_root = Path(f"out/experiments/{experiment_name}")
        experiment_root.mkdir(parents=True, exist_ok=True)
        filename = Path("ax_experiment.json")
        self.ax_client.save_to_json_file(str(experiment_root / filename))

    def save_result(self, best_parameters, exp_name):
        now_str = datetime.now().strftime("%Y%m%dT%H%M%S")
        try:
            experiment_df = self.ax_client.generation_strategy.trials_as_df
            experiment_df.to_csv(f"out/experiments/{exp_name}_{now_str}.csv", index=False)
        except ValueError as err:
            logger.warning(f"{err}")
        parameters_cfg = OmegaConf.create(best_parameters)
        experiment_root = Path(f"out/experiments/{exp_name}")
        experiment_root.mkdir(parents=True, exist_ok=True)
        OmegaConf.save(parameters_cfg, f"out/experiments/{exp_name}_{now_str}.yml")


if __name__ == "__main__":
    cfg_ = OmegaConf.load("/Users/petr/Projects/learning/petrs-tests/ax_platform/hyper_setup.yaml")
    hyperparameter_search = AxHyperparameterSearch(cfg_)
    hyperparameter_search()
