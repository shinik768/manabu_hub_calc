from tools.calc_tools import change_some_alphabets

import os
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import uuid
import sys

# 許可される桁数を増やす
sys.set_int_max_str_digits(10000)

def simplify_expressions(left_expr, right_expr):
    # 左辺と右辺の式を簡略化して返す
    return sp.simplify(left_expr), sp.simplify(right_expr)

def compute_x_values(results, var1, x_vals, var2, y_vals):
    # 変数をSymPyのシンボルとして定義
    var1 = sp.symbols(var1)
    var2 = sp.symbols(var2)
    
    # 指定された変数に対応する解を取得
    results_for_var1 = results[str(var1)]

    sols = []
    for result in results_for_var1:
        eq = sp.Eq(var1, result)
        sol_list = sp.solve(eq, var1)
        sols.extend(sol_list)

    # y_valを代入してから実数解かどうかをチェック
    for sol in sols:
        # 指定されたyの値に対してxの値を計算
        for y_val in y_vals:
            real_value = sol.subs(var2, y_val).evalf()
            if real_value.is_real:
                # 実数値の場合、x_valsに追加
                x_vals.append(real_value)

def compute_y_values(results, var1, x_vals, var2, y_vals):
    # 変数をSymPyのシンボルとして定義
    var1 = sp.symbols(var1)
    var2 = sp.symbols(var2)
    
    # 指定された変数に対応する解を取得
    results_for_var2 = results[str(var2)]

    sols = []
    for result in results_for_var2:
        eq = sp.Eq(var2, result)
        sol_list = sp.solve(eq, var2)
        sols.extend(sol_list)

    # x_valを代入してから実数解かどうかをチェック
    for sol in sols:
        # 指定されたxの値に対してyの値を計算
        for x_val in x_vals:
            real_value = sol.subs(var1, x_val).evalf()
            if real_value.is_real:
                # 実数値の場合、y_valsに追加
                y_vals.append(real_value)

def adjust_ranges_based_on_x(y_vals, x_min, x_max, x_range_is_undecided, margin_rate=0.08):
    if x_range_is_undecided:
        margin_rate=10

    # xの範囲を調整
    x_width = x_max - x_min
    x_margin = margin_rate * x_width
    x_min -= x_margin
    x_max += x_margin

    # yの範囲を調整
    try:
        y_min, y_max = min(y_vals), max(y_vals)
        y_center = np.mean(np.array([min(y_vals), max(y_vals)]))
    except:
        y_center = 0

    y_width = 3/4*x_width
    y_min = y_center - y_width*(1/2 + margin_rate)
    y_max = y_center + y_width*(1/2 + margin_rate)

    return float(y_min), float(y_max), float(x_min), float(x_max)

def adjust_ranges_based_on_y(x_vals, y_min, y_max, margin_rate=0.08):
    # xの範囲を調整
    y_width = y_max - y_min
    y_margin = margin_rate * y_width
    y_min -= y_margin
    y_max += y_margin

    # xの範囲を調整
    try:
        x_min, x_max = min(x_vals), max(x_vals)
        x_center = np.mean(np.array([min(x_vals), max(x_vals)]))
    except:
        x_center = 0

    x_width = 4/3*y_width/2
    x_min = x_center - x_width*(1/2 + margin_rate)
    x_max = x_center + x_width*(1/2 + margin_rate)

    return float(y_min), float(y_max), float(x_min), float(x_max)

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
