from tools.calc_tools import format_equation
from tools.plot_tools import (
    simplify_expressions,
    compute_x_values,
    compute_y_values,
    adjust_ranges_based_on_x,
    adjust_ranges_based_on_y,
    create_meshgrid,
    plot_contour,
    save_plot_image,
)
from tools.powerful_thread import powerful_thread

import os
import re
import time
import sympy as sp
import numpy as np

def extract_coefficients(input_string):
    # 空白の直後にある数字を抽出
    numbers = re.findall(r'\s+(\d+)', input_string)
    numbers = [float(num) for num in numbers]
    return numbers

def plot_graph(
        left_expr, right_expr, results, var1, var2,
        x_min, x_max, y_min, y_max,
        x_range_is_undecided, y_range_is_undecided
    ):
    # 左辺と右辺の式を簡略化
    left_expr, right_expr = simplify_expressions(left_expr, right_expr)

    if x_range_is_undecided and y_range_is_undecided:
        expression = sp.simplify(left_expr - right_expr)
        simple_expr = sp.simplify(sp.expand(expression))
        x, y = sp.symbols(f'{var1} {var2}')

        # 係数を辞書形式で取得
        coefficients_dict = simple_expr.as_coefficients_dict()
        coefficients = coefficients_dict.values()
        coefficients = [np.abs(coef) for coef in coefficients]
        degree = sp.Poly(simple_expr).degree(x)

        # 最小の係数を取得
        min_coefficient = min(coefficients)

        # 最大の係数を取得
        max_coefficient = max(coefficients)

        # 最小の係数を1にするための定数倍の係数
        constant_multiplier = 1 / min_coefficient

        # 定数倍
        adjusted_max_coefficient = max_coefficient * constant_multiplier

        substantial_value = adjusted_max_coefficient**(1/degree)*0.5

        x_min = -substantial_value
        x_max = substantial_value

    if y_range_is_undecided:
        # xの範囲を設定
        x_vals = np.linspace(x_min, x_max, 50)
        y_vals = []

        # スレッドを作成
        thread = powerful_thread(target=compute_y_values, args=(results, var1, x_vals, var2, y_vals))

        # スレッドを開始
        thread.start()
        
            # スレッドが10秒以内に終了するか確認
        start_time = time.time()
        while thread.is_alive():
            elapsed_time = time.time() - start_time
            if elapsed_time > 10:
                print("Time limit exceeded, terminating the thread.")
                thread.raise_exception()
                break
            time.sleep(0.1)  # 100msのスリープでCPU使用率を抑える

        # スレッドの終了を待つ
        thread.join()

        y_min, y_max, x_min, x_max = adjust_ranges_based_on_x(y_vals, x_min, x_max, x_range_is_undecided)

    elif x_range_is_undecided and not y_range_is_undecided:
        # xの範囲を設定
        y_vals = np.linspace(y_min, y_max, 50)
        x_vals = []

        # スレッドを作成
        thread = powerful_thread(target=compute_x_values, args=(results, var1, x_vals, var2, y_vals))

        # スレッドを開始
        thread.start()
        
            # スレッドが10秒以内に終了するか確認
        start_time = time.time()
        while thread.is_alive():
            elapsed_time = time.time() - start_time
            if elapsed_time > 10:
                print("Time limit exceeded, terminating the thread.")
                thread.raise_exception()
                break
            time.sleep(0.1)  # 100msのスリープでCPU使用率を抑える

        # スレッドの終了を待つ
        thread.join()

        y_min, y_max, x_min, x_max = adjust_ranges_based_on_y(x_vals, y_min, y_max)

    # メッシュグリッドを作成
    X, Y = create_meshgrid(x_min, x_max, y_min, y_max)

    # 左辺と右辺の差を計算
    Z = sp.lambdify((var1, var2), left_expr - right_expr, 'numpy')(X, Y)

    # グラフを描画
    if np.isreal(Z).all():
        plot_contour(X, Y, Z, format_equation(left_expr, right_expr), var1, var2, x_min, x_max, y_min, y_max)
    else:
        return f"{x_min}<={var1}<={x_max}の範囲内ではグラフを描画できません。"

    # 画像ファイルを保存
    image_path = save_plot_image()

    # 画像ファイルの存在を確認
    if os.path.exists(image_path):
        print(f"画像ファイルが保存されました: {image_path}")
    else:
        print("画像ファイルの保存に失敗しました。")
    
    return image_path
