if __name__ == "__main__":
    from layers import LinearLayer, ReLULayer, SigmoidLayer, SoftmaxLayer
    from losses import CrossEntropyLossLayer
    from optimizers import SGDOptimizer
    from train import plot_model_guesses, train
else:
    from .layers import LinearLayer, ReLULayer, SigmoidLayer, SoftmaxLayer
    from .optimizers import SGDOptimizer
    from .losses import CrossEntropyLossLayer
    from .train import plot_model_guesses, train

from typing import Any, Dict

import numpy as np
import torch
from matplotlib import pyplot as plt
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from utils import load_dataset, problem

RNG = torch.Generator()
RNG.manual_seed(446)


@problem.tag("hw3-A")
def crossentropy_parameter_search(
    dataset_train: TensorDataset, dataset_val: TensorDataset
) -> Dict[str, Any]:
    """
    Main subroutine of the CrossEntropy problem.
    It's goal is to perform a search over hyperparameters, and return a dictionary containing training history of models, as well as models themselves.

    Models to check (please try them in this order):
        - Linear Regression Model
        - Network with one hidden layer of size 2 and sigmoid activation function after the hidden layer
        - Network with one hidden layer of size 2 and ReLU activation function after the hidden layer
        - Network with two hidden layers (each with size 2)
            and Sigmoid, ReLU activation function after corresponding hidden layers
        - Network with two hidden layers (each with size 2)
            and ReLU, Sigmoid activation function after corresponding hidden layers
    NOTE: Each model should end with a Softmax layer due to CrossEntropyLossLayer requirement.

    Notes:
        - When choosing the number of epochs, consider effect of other hyperparameters on it.
            For example as learning rate gets smaller you will need more epochs to converge.

    Args:
        dataset_train (TensorDataset): Dataset for training.
        dataset_val (TensorDataset): Dataset for validation.

    Returns:
        Dict[str, Any]: Dictionary/Map containing history of training of all models.
            You are free to employ any structure of this dictionary, but we suggest the following:
            {
                name_of_model: {
                    "train": Per epoch losses of model on train set,
                    "val": Per epoch losses of model on validation set,
                    "model": Actual PyTorch model (type: nn.Module),
                }
            }
    """
    models = {
        "Linear Regression": [LinearLayer(2, 2), SoftmaxLayer()],
        "One Hidden Layer (Sigmoid)": [LinearLayer(2, 2), SigmoidLayer(), LinearLayer(2, 2), SoftmaxLayer()],
        "One Hidden Layer (ReLU)": [LinearLayer(2, 2), ReLULayer(), LinearLayer(2, 2), SoftmaxLayer()],
        "Two Hidden Layers (Sigmoid, ReLU)": [LinearLayer(2, 2), SigmoidLayer(), LinearLayer(2, 2), ReLULayer(), LinearLayer(2, 2), SoftmaxLayer()],
        "Two Hidden Layers (ReLU, Sigmoid)": [LinearLayer(2, 2), ReLULayer(), LinearLayer(2, 2), SigmoidLayer(), LinearLayer(2, 2), SoftmaxLayer()],
    }

    train_loader = DataLoader(dataset_train, batch_size=4, shuffle=True)
    val_loader = DataLoader(dataset_val, batch_size=4, shuffle=False)

    results = {}

    for name, layers in models.items():
        model = build_model(layers)
        criterion = CrossEntropyLossLayer()
        optimizer = SGDOptimizer(model.parameters(), lr=0.1)
        
        history = train(train_loader, model, criterion, optimizer, val_loader, epochs=100)

        results[name] = {
            "train": history["train"],
            "val": history["val"],
            "model": model,
        }

    return results


@problem.tag("hw3-A")
def accuracy_score(model, dataloader) -> float:
    """Calculates accuracy of model on dataloader. Returns it as a fraction.

    Args:
        model (nn.Module): Model to evaluate.
        dataloader (DataLoader): Dataloader for CrossEntropy.
            Each example is a tuple consiting of (observation, target).
            Observation is a 2-d vector of floats.
            Target is an integer representing a correct class to a corresponding observation.

    Returns:
        float: Vanilla python float resprenting accuracy of the model on given dataset/dataloader.
            In range [0, 1].

    Note:
        - For a single-element tensor you can use .item() to cast it to a float.
        - This is similar to MSE accuracy_score function,
            but there will be differences due to slightly different targets in dataloaders.
    """
    correct = 0
    total = 0

    with torch.no_grad():
        for x_batch, y_batch in dataloader:
            outputs = model(x_batch)
            _, predicted = torch.max(outputs, 1)
            total += y_batch.size(0)
            correct += (predicted == y_batch).sum().item()

    return correct / total


@problem.tag("hw3-A", start_line=7)
def main():
    """
    Main function of the Crossentropy problem.
    It should:
        1. Call crossentropy_parameter_search routine and get dictionary for each model architecture/configuration.
        2. Plot Train and Validation losses for each model all on single plot (it should be 10 lines total).
            x-axis should be epochs, y-axis should me Crossentropy loss, REMEMBER to add legend
        3. Choose and report the best model configuration based on validation losses.
            In particular you should choose a model that achieved the lowest validation loss at ANY point during the training.
        4. Plot best model guesses on test set (using plot_model_guesses function from train file)
        5. Report accuracy of the model on test set.

    Starter code loads dataset, converts it into PyTorch Datasets, and those into DataLoaders.
    You should use these dataloaders, for the best experience with PyTorch.
    """
    (x, y), (x_val, y_val), (x_test, y_test) = load_dataset("xor")

    dataset_train = TensorDataset(torch.from_numpy(x).float(), torch.from_numpy(y))
    dataset_val = TensorDataset(torch.from_numpy(x_val).float(), torch.from_numpy(y_val))
    dataset_test = TensorDataset(torch.from_numpy(x_test).float(), torch.from_numpy(y_test))

    ce_configs = crossentropy_parameter_search(dataset_train, dataset_val)
    
    plt.figure()
    for name, config in ce_configs.items():
        plt.plot(config['train'], label=f"{name} Train")
        plt.plot(config['val'], label=f"{name} Val")

    plt.xlabel('Epochs')
    plt.ylabel('Crossentropy Loss')
    plt.legend()
    plt.title('Crossentropy Loss for Different Models')
    plt.show()

    best_model_name = min(ce_configs, key=lambda x: min(ce_configs[x]['val']))
    best_model = ce_configs[best_model_name]['model']
    print(f"Best model: {best_model_name}")

    test_loader = DataLoader(dataset_test, batch_size=4, shuffle=False)
    plot_model_guesses(test_loader, best_model, title=f"Best Model: {best_model_name}")

    accuracy = accuracy_score(best_model, test_loader)
    print(f"Accuracy of the best model on test set: {accuracy}")


if __name__ == "__main__":
    main()
