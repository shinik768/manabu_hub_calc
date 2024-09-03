import sympy as sp
import matplotlib.pyplot as plt
import uuid
import os

# 数式を自動で画像として出力する機能をつけようか迷ったが、複雑な数式だと色々調整が大変なので今は諦める。
# ごくごく単純な数式なら下の関数で画像化できる。

# 数式を作成する
a, b, c = sp.symbols('a b c')
expression = sp.Eq(a, 3/b*c)

# 画像として保存する関数
def save_latex_as_image(expression):
    tex = sp.latex(expression)
    fig, ax = plt.subplots(figsize=(8, 6))  # サイズを調整
    ax.text(0.5, 0.5, f"${tex}$", fontsize=15, ha='center', va='center')
    ax.axis('off')  # 軸をオフにする

    # ランダムな文字列を生成して画像のパスを作成
    random_string = uuid.uuid4().hex
    image_path = os.path.join('static', f'graph_{random_string}.png')
    plt.rcParams['font.family'] = 'Times New Roman'

    # 画像をファイルとして保存
    plt.savefig(image_path, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
    plt.close(fig)
    
    return image_path

# 数式を画像として保存する
image_path = save_latex_as_image(expression)
print(f"長い数式の画像が {image_path} として保存されました。")