from typing import Tuple, Union

import matplotlib.pyplot as plt
import numpy as np

from utils import load_dataset, problem


def f_true(x: np.ndarray) -> np.ndarray:
    """True function, which was used to generate data.
    Should be used for plotting.

    Args:
        x (np.ndarray): A (n,) array. Input.

    Returns:
        np.ndarray: A (n,) array.
    """
    return 6 * np.sin(np.pi * x) * np.cos(4 * np.pi * x ** 2)


@problem.tag("hw3-A")
def poly_kernel(x_i: np.ndarray, x_j: np.ndarray, d: int) -> np.ndarray:
    """Polynomial kernel.

    Given two indices a and b it should calculate:
    K[a, b] = (x_i[a] * x_j[b] + 1)^d

    Args:
        x_i (np.ndarray): An (n,) array. Observations (Might be different from x_j).
        x_j (np.ndarray): An (m,) array. Observations (Might be different from x_i).
        d (int): Degree of polynomial.

    Returns:
        np.ndarray: A (n, m) matrix, where each element is as described above (see equation for K[a, b])

    Note:
        - It is crucial for this function to be vectorized, and not contain for-loops.
            It will be called a lot, and it has to be fast for reasonable run-time.
        - You might find .outer functions useful for this function.
            They apply an operation similar to xx^T (if x is a vector), but not necessarily with multiplication.
            To use it simply append .outer to function. For example: np.add.outer, np.divide.outer
    """
    return (np.outer(x_i, x_j) + 1) ** d


@problem.tag("hw3-A")
def rbf_kernel(x_i: np.ndarray, x_j: np.ndarray, gamma: float) -> np.ndarray:
    """Radial Basis Function (RBF) kernel.

    Given two indices a and b it should calculate:
    K[a, b] = exp(-gamma*(x_i[a] - x_j[b])^2)

    Args:
        x_i (np.ndarray): An (n,) array. Observations (Might be different from x_j).
        x_j (np.ndarray): An (m,) array. Observations (Might be different from x_i).
        gamma (float): Gamma parameter for RBF kernel. (Inverse of standard deviation)

    Returns:
        np.ndarray: A (n, m) matrix, where each element is as described above (see equation for K[a, b])

    Note:
        - It is crucial for this function to be vectorized, and not contain for-loops.
            It will be called a lot, and it has to be fast for reasonable run-time.
        - You might find .outer functions useful for this function.
            They apply an operation similar to xx^T (if x is a vector), but not necessarily with multiplication.
            To use it simply append .outer to function. For example: np.add.outer, np.divide.outer
    """
    return np.exp(-gamma * (np.subtract.outer(x_i, x_j) ** 2))


@problem.tag("hw3-A")
def train(
    x: np.ndarray,
    y: np.ndarray,
    kernel_function: Union[poly_kernel, rbf_kernel],  # type: ignore
    kernel_param: Union[int, float],
    _lambda: float,
) -> np.ndarray:
    """Trains and returns an alpha vector, that can be used to make predictions.

    Args:
        x (np.ndarray): Array of shape (n,). Observations.
        y (np.ndarray): Array of shape (n,). Targets.
        kernel_function (Union[poly_kernel, rbf_kernel]): Either poly_kernel or rbf_kernel functions.
        kernel_param (Union[int, float]): Gamma (if kernel_function is rbf_kernel) or d (if kernel_function is poly_kernel).
        _lambda (float): Regularization constant.

    Returns:
        np.ndarray: Array of shape (n,) containing alpha hat as described in the pdf.
    """
    K = kernel_function(x, x, kernel_param)
    n = len(x)
    alpha = np.linalg.solve(K + _lambda * np.eye(n), y)
    return alpha


@problem.tag("hw3-A", start_line=1)
def cross_validation(
    x: np.ndarray,
    y: np.ndarray,
    kernel_function: Union[poly_kernel, rbf_kernel],  # type: ignore
    kernel_param: Union[int, float],
    _lambda: float,
    num_folds: int,
) -> float:
    """Performs cross validation.

    In a for loop over folds:
        1. Set current fold to be validation, and set all other folds as training set.
        2, Train a function on training set, and then get mean squared error on current fold (validation set).
    Return validation loss averaged over all folds.

    Args:
        x (np.ndarray): Array of shape (n,). Observations.
        y (np.ndarray): Array of shape (n,). Targets.
        kernel_function (Union[poly_kernel, rbf_kernel]): Either poly_kernel or rbf_kernel functions.
        kernel_param (Union[int, float]): Gamma (if kernel_function is rbf_kernel) or d (if kernel_function is poly_kernel).
        _lambda (float): Regularization constant.
        num_folds (int): Number of folds. It should be either len(x) for LOO, or 10 for 10-fold CV.

    Returns:
        float: Average loss of trained function on validation sets across all folds.
    """
    fold_size = len(x) // num_folds
    errors = []
    
    for i in range(num_folds):
        val_start = i * fold_size
        val_end = val_start + fold_size
        x_val, y_val = x[val_start:val_end], y[val_start:val_end]
        x_train = np.concatenate((x[:val_start], x[val_end:]))
        y_train = np.concatenate((y[:val_start], y[val_end:]))
        
        alpha = train(x_train, y_train, kernel_function, kernel_param, _lambda)
        K_val = kernel_function(x_val, x_train, kernel_param)
        y_pred = K_val @ alpha
        error = np.mean((y_val - y_pred) ** 2)
        errors.append(error)
    
    return np.mean(errors)


@problem.tag("hw3-A")
def rbf_param_search(
    x: np.ndarray, y: np.ndarray, num_folds: int
) -> Tuple[float, float]:
    """
    Parameter search for RBF kernel.

    There are two possible approaches:
        - Grid Search - Fix possible values for lambda, loop over them and record value with the lowest loss.
        - Random Search - Fix number of iterations, during each iteration sample lambda from some distribution and record value with the lowest loss.

    Args:
        x (np.ndarray): Array of shape (n,). Observations.
        y (np.ndarray): Array of shape (n,). Targets.
        num_folds (int): Number of folds. It should be len(x) for LOO.

    Returns:
        Tuple[float, float]: Tuple containing best performing lambda and gamma pair.

    Note:
        - You do not really need to search over gamma. 1 / (median(dist(x_i, x_j)^2) for all unique pairs x_i, x_j in x
            should be sufficient for this problem. That being said you are more than welcome to do so.
        - If using random search we recommend sampling lambda from distribution 10**i, where i~Unif(-5, -1)
        - If using grid search we recommend choosing possible lambdas to 10**i, where i=linspace(-5, -1)
    """
    gamma = 1 / np.median(np.subtract.outer(x, x) ** 2)
    best_lambda = None
    best_loss = float('inf')
    
    lambdas = 10 ** np.linspace(-5, -1, 50)
    
    for _lambda in lambdas:
        loss = cross_validation(x, y, rbf_kernel, gamma, _lambda, num_folds)
        if loss < best_loss:
            best_loss = loss
            best_lambda = _lambda
    
    return best_lambda, gamma


@problem.tag("hw3-A")
def poly_param_search(
    x: np.ndarray, y: np.ndarray, num_folds: int
) -> Tuple[float, int]:
    """
    Parameter search for Poly kernel.

    There are two possible approaches:
        - Grid Search - Fix possible values for lambdas and ds.
            Have nested loop over all possibilities and record value with the lowest loss.
        - Random Search - Fix number of iterations, during each iteration sample lambda, d from some distributions and record value with the lowest loss.

    Args:
        x (np.ndarray): Array of shape (n,). Observations.
        y (np.ndarray): Array of shape (n,). Targets.
        num_folds (int): Number of folds. It should be either len(x) for LOO, or 10 for 10-fold CV.

    Returns:
        Tuple[float, int]: Tuple containing best performing lambda and d pair.

    Note:
        - If using random search we recommend sampling lambda from distribution 10**i, where i~Unif(-5, -1)
            and d from distribution [5, 6, ..., 24, 25]
        - If using grid search we recommend choosing possible lambdas to 10**i, where i=linspace(-5, -1)
            and possible ds to [5, 6, ..., 24, 25]
    """
    best_lambda = None
    best_d = None
    best_loss = float('inf')
    
    lambdas = 10 ** np.linspace(-5, -1, 50)
    degrees = range(5, 26)
    
    for _lambda in lambdas:
        for d in degrees:
            loss = cross_validation(x, y, poly_kernel, d, _lambda, num_folds)
            if loss < best_loss:
                best_loss = loss
                best_lambda = _lambda
                best_d = d
    
    return best_lambda, best_d

@problem.tag("hw3-A", start_line=1)
def main():
    """
    Main function of the problem

    It should:
        A. Using x_30, y_30, rbf_param_search and poly_param_search report optimal values for lambda (for rbf), gamma, lambda (for poly) and d.
            Note that x_30, y_30 has been loaded in for you. You do not need to use (x_300, y_300) or (x_1000, y_1000).
        B. For both rbf and poly kernels, train a function using x_30, y_30 and plot predictions on a fine grid

    Note:
        - In part b fine grid can be defined as np.linspace(0, 1, num=100)
        - When plotting you might find that your predictions go into hundreds, causing majority of the plot to look like a flat line.
            To avoid this call plt.ylim(-6, 6).
    """
    (x_30, y_30), (x_300, y_300), (x_1000, y_1000) = load_dataset("kernel_bootstrap")
    best_lambda_rbf, best_gamma = rbf_param_search(x_30, y_30, len(x_30))
    best_lambda_poly, best_d = poly_param_search(x_30, y_30, 10)
    
    fine_grid = np.linspace(0, 1, num=100)
    
    alpha_rbf = train(x_30, y_30, rbf_kernel, best_gamma, best_lambda_rbf)
    K_rbf = rbf_kernel(fine_grid, x_30, best_gamma)
    y_rbf = K_rbf @ alpha_rbf
    
    plt.figure(figsize=(10, 5))
    plt.plot(fine_grid, f_true(fine_grid), label="True function")
    plt.plot(fine_grid, y_rbf, label="RBF Kernel Prediction")
    plt.scatter(x_30, y_30, color='red', label="Data points")
    plt.ylim(-6, 6)
    plt.legend()
    plt.title("RBF Kernel")
    plt.show()
    
    alpha_poly = train(x_30, y_30, poly_kernel, best_d, best_lambda_poly)
    K_poly = poly_kernel(fine_grid, x_30, best_d)
    y_poly = K_poly @ alpha_poly
    
    plt.figure(figsize=(10, 5))
    plt.plot(fine_grid, f_true(fine_grid), label="True function")
    plt.plot(fine_grid, y_poly, label="Poly Kernel Prediction")
    plt.scatter(x_30, y_30, color='red', label="Data points")
    plt.ylim(-6, 6)
    plt.legend()
    plt.title("Polynomial Kernel")
    plt.show()


if __name__ == "__main__":
    main()
