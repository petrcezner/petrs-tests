import configparser
from pathlib import Path
from typing import Tuple, Union

import torch
import torchmetrics
import torchvision.models as models
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader
import pytorch_lightning as pl


def train_transform(
        flip: bool = True,
        crop: int = 224,
        mean: list = [0.485, 0.456, 0.406],
        std: list = [0.229, 0.224, 0.225],
):
    if flip:
        transform = transforms.Compose(
            [
                transforms.RandomResizedCrop(crop),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize(mean, std),
            ]
        )
    else:
        transform = transforms.Compose(
            [
                transforms.RandomResizedCrop(crop),
                transforms.ToTensor(),
                transforms.Normalize(mean, std),
            ]
        )
    return transform


def test_transform(
        resize: int = 256,
        crop: int = 224,
        mean: list = [0.485, 0.456, 0.406],
        std: list = [0.229, 0.224, 0.225],
):
    transform = transforms.Compose(
        [
            transforms.Resize(resize),
            transforms.CenterCrop(crop),
            transforms.ToTensor(),
            transforms.Normalize(mean, std),
        ]
    )
    return transform


class ResnetClassifier(pl.LightningModule):
    def __init__(
            self,
            num_classes: int,
            train_path: Path,
            vld_path: Path,
            test_path: Path = None,
            resnet: str = "resnet18",
            optimizer: str = "adam",
            lr: float = 1e-3,
            batch_size: int = 16,
            transfer: str = "DEFAULT",
            tune_fc_only: bool = True,
            momentum: Union[Tuple[float, float], float] = (0.9, 0.999),
            weight_decay: float = 0
    ):
        super().__init__()

        self.__dict__.update(locals())
        resnets = {
            "resnet18": models.resnet18,
            "resnet34": models.resnet34,
            "resnet50": models.resnet50,
            "resnet101": models.resnet101,
            "resnet152": models.resnet152,
            "resnext50": models.resnext50_32x4d,
            "resnext101": models.resnext101_32x8d,
            "wide_resnet50": models.wide_resnet50_2,
            "wide_resnet101": models.wide_resnet101_2,
        }
        self.model = resnets[resnet](weights=transfer)
        optimizers = {"adam": torch.optim.Adam, "sgd": torch.optim.SGD}
        optimizer_args = {'adam': 'betas', 'sgd': 'momentum'}
        self.optimizer = optimizers.get(optimizer, 'adam')
        self.optimizer_args = {optimizer_args[optimizer]: momentum,
                               'weight_decay': weight_decay,
                               'lr': self.lr}
        self.criterion = (
            torch.nn.BCEWithLogitsLoss()
            if num_classes == 2
            else torch.nn.CrossEntropyLoss()
        )

        linear_size = list(self.model.children())[-1].in_features
        self.model.fc = torch.nn.Linear(linear_size, num_classes)

        self.train_acc = torchmetrics.Accuracy(num_classes=num_classes)
        self.valid_acc = torchmetrics.Accuracy(num_classes=num_classes)

        if tune_fc_only:
            for child in list(self.model.children())[:-1]:
                for param in child.parameters():
                    param.requires_grad = False

    def forward(self, X):
        return self.model(X)

    def configure_optimizers(self):
        optimizer = self.optimizer(self.parameters(), **self.optimizer_args)
        return optimizer

    def train_dataloader(self):
        transform = train_transform()
        img_train = ImageFolder(self.train_path, transform=transform)
        return DataLoader(img_train, batch_size=self.batch_size, shuffle=True)

    def training_step(self, batch, batch_idx):
        x, y = batch
        preds = self(x)
        if self.num_classes == 2:
            y = torch.nn.functional.one_hot(y, num_classes=2).float()

        loss = self.criterion(preds, y)
        if self.num_classes == 2:
            self.train_acc(preds, y.to(torch.long))
        else:
            self.train_acc(preds, y)
        self.log(
            "train_loss", loss, on_step=True, on_epoch=True, prog_bar=True, logger=True
        )
        self.log(
            "train_acc",
            self.train_acc,
            on_step=True,
            on_epoch=False,
            prog_bar=True,
            logger=True,
        )
        return loss

    def val_dataloader(self):
        transform = test_transform()

        img_val = ImageFolder(self.vld_path, transform=transform)

        return DataLoader(img_val, batch_size=1, shuffle=False)

    def validation_step(self, batch, batch_idx):
        loss = self._shared_eval_step(batch, batch_idx)
        self.log("val_loss", loss, on_epoch=True, prog_bar=True, logger=True)
        self.log("val_acc", self.valid_acc, on_epoch=True, prog_bar=True, logger=True)
        return loss, self.valid_acc

    def test_dataloader(self):
        transform = test_transform()

        img_test = ImageFolder(self.test_path, transform=transform)

        return DataLoader(img_test, batch_size=1, shuffle=False)

    def test_step(self, batch, batch_idx):
        loss = self._shared_eval_step(batch, batch_idx)
        self.log("test_loss", loss, on_step=True, prog_bar=True, logger=True)
        self.log("test_acc", self.valid_acc, on_step=True, prog_bar=True, logger=True)

    def _shared_eval_step(self, batch, batch_idx):
        x, y = batch
        preds = self(x)
        if self.num_classes == 2:
            y = torch.nn.functional.one_hot(y, num_classes=2).float()

        loss = self.criterion(preds, y)
        if self.num_classes == 2:
            self.valid_acc(preds, y.to(torch.long))
        else:
            self.valid_acc(preds, y)
        return loss


def _get_trainer(
        max_epochs: int = 1000,
        use_gpus: bool = True,
        devices: int = 1,
        accelerator: str = "cpu",
        early_stop: pl.callbacks = None,
        model_checkpoint: pl.callbacks = None,
):
    callbacks = [early_stop, model_checkpoint]

    trainer = pl.Trainer(
        accelerator=accelerator,
        max_epochs=max_epochs,
        callbacks=callbacks,
        auto_select_gpus=use_gpus,
        devices=devices,
    )
    return trainer


def fit(
        num_classes: int,
        train_path: Path,
        vld_path: Path,
        test_path: Path = None,
        resnet: str = "resnet18",
        optimizer: str = "adam",
        lr: float = 1e-3,
        batch_size: int = 16,
        transfer: str = "DEFAULT",
        tune_fc_only: bool = True,
        max_epochs: int = 1000,
        use_gpus: bool = True,
        devices: int = 1,
        accelerator: str = "cpu",
        pretrained: bool = False,
        checkpoint_path: Path = None,
):
    early_stop = pl.callbacks.EarlyStopping(
        monitor="train_loss",
        min_delta=0.01,
        patience=200,
        verbose=True,
        mode="min",
        check_on_train_epoch_end=True,
    ),
    model_checkpoint = pl.callbacks.ModelCheckpoint(
        monitor="train_loss", save_top_k=1, mode="min"
    )
    trainer = _get_trainer(
        max_epochs=max_epochs,
        use_gpus=use_gpus,
        devices=devices,
        accelerator=accelerator,
        early_stop=early_stop,
        model_checkpoint=model_checkpoint,
    )
    if pretrained:
        model = ResnetClassifier.load_from_checkpoint(
            checkpoint_path,
            num_classes=num_classes,
            train_path=train_path,
            vld_path=vld_path,
            test_path=test_path,
            resnet=resnet,
            optimizer=optimizer,
            lr=lr,
            batch_size=batch_size,
            transfer=transfer,
            tune_fc_only=tune_fc_only,
        )
    else:
        model = ResnetClassifier(
            num_classes=num_classes,
            train_path=train_path,
            vld_path=vld_path,
            test_path=test_path,
            resnet=resnet,
            optimizer=optimizer,
            lr=lr,
            batch_size=batch_size,
            transfer=transfer,
            tune_fc_only=tune_fc_only,
        )

    trainer.fit(model)
    return model


def test(
        model,
        max_epochs: int = 1000,
        use_gpus: bool = True,
        devices: bool = True,
        accelerator: str = "cpu",
        early_stop: transforms.Compose = None,
        model_checkpoint: transforms.Compose = None,
):
    trainer = _get_trainer(
        max_epochs, use_gpus, devices, accelerator, early_stop, model_checkpoint
    )
    trainer.test(model)


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    from torch.utils.data import DataLoader
    from torchvision.datasets import ImageFolder

    # -d /Users/petr/Projects/datasentics/datasets/alien_vs_predator_thumbnails/data -n 2 -c lightning_logs/version_0/checkpoints/epoch=136-step=6028.ckpt
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--train",
        action="store_true",
        help="If true, model is train on dataset provided by arguments. Else, detection is preformed.",
    )
    parser.add_argument(
        "-d", "--data_path", type=Path, default="", help="Path to data folder. It is expected, that the folder for"
                                                         " training is named: training, for validation: validation."
    )
    parser.add_argument('--predict_with_class', action='store_true',
                        help='If true, model returns images with detection dictionary.')
    parser.add_argument(
        "-c",
        "--checkpoint_path",
        type=Path,
        default="./lightning_logs/",
        help="Path to saved checkpoint",
    )
    parser.add_argument("-n", "--num_classes", type=int, default=10, help="Number of classes in data")
    args = parser.parse_args()

    dataset = ImageFolder(
        Path(args.data_path / "validation"),
        transform=transforms.Compose([transforms.Resize(256), transforms.ToTensor()]),
    )

    if args.train:
        model_ = fit(
            num_classes=args.num_classes,
            train_path=Path(args.data_path / "train"),
            vld_path=Path(args.data_path / "validation"),
            test_path=Path(args.data_path / "validation"),
            resnet="resnet50",
            optimizer="adam",
            lr=1e-3,
            batch_size=16,
            transfer="DEFAULT",
            tune_fc_only=True,
            max_epochs=1000,
            use_gpus=True,
            devices=1,
            accelerator="auto",
            pretrained=False,
            checkpoint_path=Path(args.checkpoint_path),
        )
