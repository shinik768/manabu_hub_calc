from tools.calc_tools import change_some_alphabets

import os
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import uuid

def simplify_expressions(left_expr, right_expr):
    # 左辺と右辺の式を簡略化して返す
    return sp.simplify(left_expr), sp.simplify(right_expr)

def compute_y_values(left_expr, right_expr, var1, x_vals, var2):
    # 与えられたxの値に対するyの値を計算する
    y_vals = []
    for x in x_vals:
        y_vals_at_x = sp.solve(left_expr.subs(var1, x) - right_expr, var2)
        y_vals.extend([float(sol.evalf()) for sol in y_vals_at_x if sol.is_real])
    return y_vals

def adjust_ranges(y_vals, x_min, x_max, margin_rate=0.08):
    # yの値に基づいてxおよびyの範囲を調整する
    if not y_vals:
        return None, None, None, None

    y_min, y_max = min(y_vals), max(y_vals)
    y_margin = margin_rate * (y_max - y_min)
    y_min -= y_margin
    y_max += y_margin

    x_margin = margin_rate * (x_max - x_min)
    x_min -= x_margin
    x_max += x_margin

    return y_min, y_max, x_min, x_max

def create_meshgrid(x_min, x_max, y_min, y_max):
    # 指定された範囲に基づいてメッシュグリッドを作成する
    x_vals_for_plot = np.linspace(x_min, x_max, 400)
    y_vals_for_plot = np.linspace(y_min, y_max, 400)
    return np.meshgrid(x_vals_for_plot, y_vals_for_plot)

def plot_contour(X, Y, Z, graph_title, var1, var2, x_min, x_max, y_min, y_max):
    # 等高線グラフを描画する
    plt.figure(figsize=(8, 6))
    plt.contour(X, Y, Z, levels=[0], colors='blue')
    plt.title(change_some_alphabets(graph_title))
    plt.xlabel(change_some_alphabets(var1))
    plt.ylabel(change_some_alphabets(var2))
    plt.grid()
    plt.axhline(0, color='black', linewidth=0.5, ls='--')
    plt.axvline(0, color='black', linewidth=0.5, ls='--')
    plt.xlim([x_min, x_max])
    plt.ylim([y_min, y_max])

def save_plot_image():
    # ランダムな文字列を生成してグラフを保存する
    random_string = uuid.uuid4().hex
    image_path = os.path.join('static', f'graph_{random_string}.png')
    plt.savefig(image_path)
    plt.close()
    return image_path
