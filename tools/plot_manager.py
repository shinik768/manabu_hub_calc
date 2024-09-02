from tools.calc_tools import format_equation
from tools.plot_tools import (
    simplify_expressions,
    adjust_xy_ranges_based_on_x,
    adjust_xy_ranges_based_on_y,
    create_meshgrid,
    plot_contour,
    save_plot_image,
    designate_x_range_automatically,
    designate_x_range_based_on_y,
    designate_y_range_based_on_x,
)

import os
import sympy as sp
import numpy as np

def plot_graph(
        left_expr, right_expr, results, x, y,
        x_min, x_max, y_min, y_max,
        x_range_is_undecided, y_range_is_undecided
    ):
    # 左辺と右辺の式を簡略化
    left_expr, right_expr = simplify_expressions(left_expr, right_expr)

    if x_range_is_undecided and y_range_is_undecided:
        x_min, x_max = designate_x_range_automatically(left_expr, right_expr, x, y)

    if y_range_is_undecided:
        x_min, x_max, y_min, y_max = designate_y_range_based_on_x(
            x, y, results, x_min, x_max, x_range_is_undecided)

    elif x_range_is_undecided and not y_range_is_undecided:
        x_min, x_max, y_min, y_max = designate_x_range_based_on_y(
            x, y, results, y_min, y_max)

    # メッシュグリッドを作成
    X, Y = create_meshgrid(x_min, x_max, y_min, y_max)

    # 左辺と右辺の差を計算
    Z = sp.lambdify((x, y), left_expr - right_expr, 'numpy')(X, Y)

    # グラフを描画
    if np.isreal(Z).all():
        plot_contour(X, Y, Z, format_equation(left_expr, right_expr), x, y, x_min, x_max, y_min, y_max)
    else:
        return f"{x_min}<={x}<={x_max}の範囲内ではグラフを描画できません。"

    # 画像ファイルを保存
    image_path = save_plot_image()

    # 画像ファイルの存在を確認
    if os.path.exists(image_path):
        print(f"画像ファイルが保存されました: {image_path}")
    else:
        print("画像ファイルの保存に失敗しました。")
    
    return image_path