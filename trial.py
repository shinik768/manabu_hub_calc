import os
import sympy as sp
import time
import re
import numpy as np
import matplotlib.pyplot as plt

def add_spaces(expression):
    expression = re.sub(r'(?<=[^\s\+\-])(?=[\+\-])', ' ', expression)
    return expression

def add_multiplication_sign(expression):
    expression = re.sub(r'(?<=[\d])(?=[a-zA-Z])', '*', expression)  # 数字と変数の間
    expression = re.sub(r'(?<=[a-zA-Z])(?=[a-zA-Z])', '*', expression)  # 変数と変数の間
    expression = re.sub(r'(?<=[)])(?=[a-zA-Z])', '*', expression)  # 括弧と変数の間
    expression = re.sub(r'(?<=[\d])(?=[(])', '*', expression)  # 数字と括弧の間
    expression = re.sub(r'(?<=[a-zA-Z])(?=[(])', '*', expression)  # 変数と括弧の間
    expression = re.sub(r'(?<=[)])(?=[(])', '*', expression)  # 括弧と括弧の間
    return expression

def add_exponentiation_sign(expression):
    expression = str(expression).replace('^', '**') # ^を**に変換
    expression = re.sub(r'(?<=[a-zA-Z])(?=\d)', '**', expression)  # 文字と数字の間
    expression = re.sub(r'(?<=[)])(?=\d)', '**', expression)  # 括弧と数字の間
    return expression

def sort_expression(expression):
    # 式中に含まれる変数を取得
    variables = sorted(expression.free_symbols, key=lambda var: str(var))
    
    # 式が変数を含まない場合、そのまま返す
    if not variables:
        return expression

    terms = expression.as_ordered_terms()
    
    def get_sort_key(term):
        poly = sp.Poly(term, *variables) if term.free_symbols else sp.Poly(term)
        return (poly.total_degree(), term.as_coefficients_dict().keys())

    sorted_terms = sorted(terms, key=get_sort_key)
    
    sorted_expr = sp.Add(*sorted_terms)
    return sorted_expr

def format_expression(expression):
    expanded_expr = sp.expand(sp.sympify(expression))  # 展開
    simplified_expr = sp.simplify(expanded_expr)  # 簡略化
    sorted_expr = sort_expression(simplified_expr)
    formatted_expr = str(sorted_expr).replace('**', '^').replace('*', '')
    return formatted_expr

def format_equation(left_expr, right_expr):
    left_minus_right_expr = left_expr - right_expr  # 左辺と右辺の差を簡略化
    formatted_expr = format_expression(left_minus_right_expr)
    return f"{formatted_expr} = 0"

def plot_graph(left_expr, right_expr, var1, var2):
    # 変数の範囲を設定
    x_vals = np.linspace(-10, 10, 400)  # xの範囲
    y_vals = np.linspace(-10, 10, 400)  # yの範囲
    X, Y = np.meshgrid(x_vals, y_vals)

    # タイトルを指定
    graph_title = format_equation(left_expr, right_expr)

    # 左辺と右辺の差を計算
    Z = sp.lambdify((var1, var2), left_expr - right_expr, 'numpy')(X, Y)  # Z = 0 になる部分を計算

    plt.figure(figsize=(8, 6))
    plt.contour(X, Y, Z, levels=[0], colors='blue')  # 等高線を描画
    plt.title(graph_title)
    plt.xlabel(var1)
    plt.ylabel(var2)
    plt.grid()
    plt.axhline(0, color='black', linewidth=0.5, ls='--')
    plt.axvline(0, color='black', linewidth=0.5, ls='--')
    plt.show

def simplify_or_solve(expression):
    try:
        expression = add_spaces(expression)
        expression = add_multiplication_sign(expression)
        expression = add_exponentiation_sign(expression)

        equal_sign_count = expression.count('=')

        if equal_sign_count == 1:
            left_side, right_side = expression.split('=')
            left_expr = sp.sympify(left_side.strip())
            right_expr = sp.sympify(right_side.strip())

            # 変数の取得
            variables = list(left_expr.free_symbols.union(right_expr.free_symbols))
            eq = sp.Eq(left_expr - right_expr, 0)
            solutions = {var: sp.solve(eq, var) for var in variables}
            # 解の表示形式を調整
            result = ""
            for var, sols in sorted(solutions.items(), key=lambda x: str(x[0])):
                if isinstance(sols, list):
                    for sol in sols:
                        result += f"{var} = {sol}\n"
                else:
                    result += f"{var} = {sols}\n"
            
            result_str = result.strip() if result else "解なし" # 解がない場合の処理
            result_str = str(result_str).replace('**', '^').replace('*', '')  # 形式を整形
            if len (variables) != 2:
                return result_str
            else:
                var1, var2 = sorted(variables, key=lambda v: str(v))  # アルファベット順でソート
                return result_str  # 画像パスを返す

        elif equal_sign_count > 1:
            return "方程式には等号 (=) をちょうど1個含めてください！"
        else:
            expanded_expr = sp.expand(sp.sympify(expression))  # 展開
            simplified_expr = sp.simplify(expanded_expr)  # 簡略化
            simplified_expr_str = str(simplified_expr).replace('**', '^').replace('*', '')  # 形式を整形
            return f"{simplified_expr_str}"

    except (sp.SympifyError, TypeError) as e:
        print(f"SymPy error: {e}")
        return "数式を正しく入力してください！"
    
print(simplify_or_solve("2a+3b^2+4c^3+5d^4=6"))