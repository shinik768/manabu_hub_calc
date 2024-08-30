from  tools.calc_tools import (
    change_I_and_i,
    format_equation,
)

import os
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import uuid

def plot_graph(left_expr, right_expr, var1, var2, x_min=-5, x_max=5):
    # 先に計算
    left_expr = sp.simplify(left_expr)
    right_expr = sp.simplify(right_expr)
    print(left_expr)
    print(right_expr)

    # 変数の範囲を設定
    x_vals = np.linspace(x_min, x_max, 50)  # val1 (x) の範囲を50個の値に分割

    # 端に余分を持たせる割合を設定
    margin_rate = 0.08
    
    # val1 に対する val2 の値を計算
    y_vals = []
    
    for x in x_vals:
        y_vals_at_x = sp.solve(left_expr.subs(var1, x) - right_expr, var2)
        # 実数の解を数値に変換しリストに追加
        y_vals.extend([float(sol.evalf()) for sol in y_vals_at_x if sol.is_real])
    
    # 解が存在しない場合のエラーハンドリング
    if not y_vals:
        return f"{x_min}<={var1}<={x_max}の範囲内ではグラフを描画できません。"

    # y_vals の最小値と最大値を取得
    y_min = min(y_vals)
    y_max = max(y_vals)

    # 5%の余裕を追加
    y_margin = margin_rate * (y_max - y_min)
    y_min -= y_margin
    y_max += y_margin

    x_margin = margin_rate * (x_max - x_min)
    x_min -= x_margin
    x_max += x_margin

    print(f"最小値: {y_min}, 最大値: {y_max}")
    
    # タイトルを指定
    graph_title = format_equation(left_expr, right_expr)
    graph_title = change_I_and_i(graph_title)

    # グラフを描画するための範囲を設定
    x_vals_for_plot = np.linspace(x_min, x_max, 400)
    y_vals_for_plot = np.linspace(y_min, y_max, 400)
    X, Y = np.meshgrid(x_vals_for_plot, y_vals_for_plot)

    # 左辺と右辺の差を計算
    Z = sp.lambdify((var1, var2), left_expr - right_expr, 'numpy')(X, Y)

    # グラフの設定と描画
    plt.figure(figsize=(8, 6))  # 4:3のアスペクト比で図を作成
    plt.contour(X, Y, Z, levels=[0], colors='blue')  # 等高線を描画
    plt.title(graph_title)
    plt.xlabel(var1)
    plt.ylabel(var2)
    plt.grid()
    plt.axhline(0, color='black', linewidth=0.5, ls='--')
    plt.axvline(0, color='black', linewidth=0.5, ls='--')
    plt.xlim([x_min, x_max])  # val1 (x) の範囲
    plt.ylim([y_min, y_max])  # val2 (y) の範囲を調整

    # ランダムな文字列を生成して画像を保存
    random_string = uuid.uuid4().hex  # ランダムな文字列を生成
    image_path = os.path.join('static', f'graph_{random_string}.png')  # staticフォルダに保存
    plt.savefig(image_path)
    plt.close()

    # 画像ファイルの存在を確認
    if os.path.exists(image_path):
        print(f"画像ファイルが保存されました: {image_path}")
    else:
        print("画像ファイルの保存に失敗しました。")
    
    return image_path