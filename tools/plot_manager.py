from tools.calc_tools import format_equation
from tools.plot_tools import (
    simplify_expressions,
    compute_y_values,
    adjust_ranges,
    create_meshgrid,
    plot_contour,
    save_plot_image,
)

import os
import sympy as sp
import numpy as np

def plot_graph(left_expr, right_expr, var1, var2, x_min=-5, x_max=5):
    # 先に計算
    left_expr, right_expr = simplify_expressions(left_expr, right_expr)
    print(left_expr)
    print(right_expr)

    # 変数の範囲を設定
    x_vals = np.linspace(x_min, x_max, 50)  # val1 (x) の範囲を50個の値に分割

    # val1 に対する val2 の値を計算
    y_vals = compute_y_values(left_expr, right_expr, var1, x_vals, var2)

    # 解が存在しない場合のエラーハンドリング
    if not y_vals:
        return f"{x_min}<={var1}<={x_max}の範囲内ではグラフを描画できません。"

    # 範囲を調整
    y_min, y_max, x_min, x_max = adjust_ranges(y_vals, x_min, x_max)

    print(f"最小値: {y_min}, 最大値: {y_max}")

    # グラフを描画するための範囲を設定
    X, Y = create_meshgrid(x_min, x_max, y_min, y_max)

    # 左辺と右辺の差を計算
    Z = sp.lambdify((var1, var2), left_expr - right_expr, 'numpy')(X, Y)

    # グラフを描画
    plot_contour(X, Y, Z, format_equation(left_expr, right_expr), var1, var2, x_min, x_max, y_min, y_max)

    # 画像ファイルを保存
    image_path = save_plot_image()

    # 画像ファイルの存在を確認
    if os.path.exists(image_path):
        print(f"画像ファイルが保存されました: {image_path}")
    else:
        print("画像ファイルの保存に失敗しました。")
    
    return image_path