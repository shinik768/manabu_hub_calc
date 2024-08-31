import threading
import sympy as sp
import re

class TimeoutException(Exception):
    pass

def clean_expression(expression):
    # 許可された文字だけを残す
    cleaned_expression = re.sub(r'[^a-zA-Z0-9=()!$+*-/*^]', '', expression)
    return cleaned_expression

def change_some_alphabets(expression):
    # ユニコードの非表示文字を使って 'i' と 'I' を入れ替え
    placeholder = '\u2063'
    expression = str(expression).replace('i', placeholder)
    expression = expression.replace('I', 'i')
    expression = expression.replace(placeholder, 'I')
    expression = str(expression).replace('E_var', placeholder)
    expression = expression.replace('E', 'E_var')
    expression = expression.replace(placeholder, 'E')
    expression = str(expression).replace('Q_var', placeholder)
    expression = expression.replace('Q', 'Q_var')
    expression = expression.replace(placeholder, 'Q')
    expression = str(expression).replace('S_var', placeholder)
    expression = expression.replace('S', 'S_var')
    expression = expression.replace(placeholder, 'S')
    return expression

def add_spaces(expression):
    # 演算子の前にスペースを追加
    expression = re.sub(r'(?<=[^\s\+\-])(?=[\+\-])', ' ', expression)
    return expression

def add_multiplication_sign(expression):
    # 乗算演算子を追加
    expression = re.sub(r'(?<=[\d])(?=[a-zA-Z])', '*', expression)
    expression = re.sub(r'(?<=[a-zA-Z])(?=[a-zA-Z])', '*', expression)
    expression = re.sub(r'(?<=[)])(?=[a-zA-Z])', '*', expression)
    expression = re.sub(r'(?<=[\d])(?=[(])', '*', expression)
    expression = re.sub(r'(?<=[a-zA-Z])(?=[(])', '*', expression)
    expression = re.sub(r'(?<=[)])(?=[(])', '*', expression)
    return expression

def add_exponentiation_sign(expression):
    # 指数演算子を追加
    expression = str(expression).replace('^', '**')
    expression = re.sub(r'(?<=[a-zA-Z])(?=\d)', '**', expression)
    expression = re.sub(r'(?<=[)])(?=\d)', '**', expression)
    return expression

def sort_expression(expression):
    # 変数を取得してソート
    variables = sorted(expression.free_symbols, key=lambda var: str(var))
    
    if not variables:
        return expression

    terms = expression.as_ordered_terms()
    
    def get_sort_key(term):
        # ソート用のキーを取得
        if term.free_symbols:
            return (sp.Poly(term, *variables).total_degree(), term.as_coefficients_dict().keys())
        else:
            return (0, term.as_coefficients_dict().keys())

    sorted_terms = sorted(terms, key=get_sort_key)
    sorted_expr = sp.Add(*sorted_terms)
    return sorted_expr

def format_expression(expression):
    # 式を展開し簡略化
    expanded_expr = sp.expand(sp.sympify(expression))
    simplified_expr = sp.simplify(expanded_expr)
    sorted_expr = sort_expression(simplified_expr)
    formatted_expr = str(sorted_expr).replace('**', '^').replace('*', '')
    return formatted_expr

def format_equation(left_expr, right_expr):
    # 左辺と右辺の差を簡略化してフォーマット
    left_minus_right_expr = sp.simplify(left_expr - right_expr)
    formatted_expr = format_expression(left_minus_right_expr)
    return f"{formatted_expr} = 0"

def clean_and_prepare_expression(expression):
    # 式をクリーニングして準備
    expression = clean_expression(expression)
    expression = add_spaces(expression)
    expression = add_multiplication_sign(expression)
    expression = add_exponentiation_sign(expression)
    expression = change_some_alphabets(expression)
    return expression

def get_variable_range(parts):
    # 変数の範囲を取得
    var1_min, var1_max = -5, 5
    if len(parts) == 3:
        try:
            var1_min, var1_max = sorted(float(num) for num in parts[1:3])
        except ValueError as e:
            print(e)
    return var1_min, var1_max

def solve_equation_in_threads(eq, variables):
    # スレッドを使用して方程式を解く
    results = []
    threads = [threading.Thread(target=solve_equation, args=(eq, var, results)) for var in variables]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join(timeout=10)
        if thread.is_alive():
            print("解を求めるのに時間がかかりすぎました。")
            raise TimeoutException("解を求めるのに時間がかかりすぎました。")
    
    return results

def format_solutions(variables, results):
    # 解をフォーマット
    sorted_results = [
        f"{var} = {results[variables.index(var)]}" if not isinstance(results[variables.index(var)], list) 
        else "\n".join(f"{var} = {sol}" for sol in results[variables.index(var)])
        for var in sorted(variables, key=str)
    ]
    result_str =  str("\n".join(sorted_results) or "解なし").replace('**', '^').replace('*', '')
    return result_str

def solve_equation(eq, var, results):
    # 方程式を解いて結果を格納
    try:
        solution = sp.solve(eq, var)
        results.append(solution)
    except Exception as e:
        print(f"解を求める際にエラーが発生しました: {e}")
        results.append("解なし")
