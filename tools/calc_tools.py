from tools.powerful_thread import powerful_thread

import sympy as sp
import re
import time
import sys

# 許可される桁数を増やす
sys.set_int_max_str_digits(10000)

def zenkaku_to_hankaku(text):
    # 全角数字とアルファベットを対応する半角文字に変換する
    zenkaku_numbers = "０１２３４５６７８９"
    hankaku_numbers = "0123456789"
    
    zenkaku_alphabets = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ" + "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
    hankaku_alphabets = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "abcdefghijklmnopqrstuvwxyz"
    
    # 全角記号と対応する半角記号を定義（面倒なので中括弧、大括弧もここで置き換える）
    zenkaku_symbols = "＝（）．×÷！＋－ー−＊／＾％{}[]"
    hankaku_symbols = "=().×÷!+---*/^%()()"
    
    # 変換テーブルを作成
    translation_table = str.maketrans(
        zenkaku_numbers + zenkaku_alphabets + zenkaku_symbols,
        hankaku_numbers + hankaku_alphabets + hankaku_symbols
    )
    
    return text.translate(translation_table)

def clean_expression(expression):
    # 許可された文字だけを残す
    cleaned_expression = re.sub(r'[^a-zA-Z0-9=().×÷!+\-*/^%]', '', expression)
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

def change_some_operators(expression):
    expression = str(expression.replace('×', '*'))
    expression = str(expression.replace('÷', '/'))
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
    expression = zenkaku_to_hankaku(expression)
    expression = clean_expression(expression)
    expression = change_some_operators(expression)
    expression = add_spaces(expression)
    expression = add_multiplication_sign(expression)
    expression = add_exponentiation_sign(expression)
    expression = change_some_alphabets(expression)
    return expression

def get_variable_range(parts):
    # 変数の範囲を取得
    var1_min, var1_max = -5,5
    var2_min, var2_max = -5,5
    var1_range_is_undecided = True
    var2_range_is_undecided = True
    if len(parts) >= 3:
        try:
            var1_min, var1_max = sorted(float(num) for num in parts[1:3] if all(parts[1:3]))
            var1_range_is_undecided = False
        except ValueError:
            pass
    if len(parts) >= 5:
        try:
            var2_min, var2_max = sorted(float(num) for num in parts[3:5] if all(parts[3:5]))
            var2_range_is_undecided = False
        except ValueError:
            pass
    return var1_min, var1_max, var2_min, var2_max, var1_range_is_undecided, var2_range_is_undecided

def solve_equation_in_threads(eq, variables):
    # スレッドを使用して方程式を解く
    results = {}
    threads = [powerful_thread(target=solve_equation, args=(eq, var, results)) for var in variables]
    is_terminated = False
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        # スレッドが10秒以内に終了するか確認
        start_time = time.time()
        if thread.is_alive():
            elapsed_time = time.time() - start_time
            if elapsed_time > 10:
                is_terminated = True
                print("Time limit exceeded, terminating the thread.")
                thread.raise_exception()
                break
            time.sleep(0.1)  # 100msのスリープでCPU使用率を抑える
    
    # 全てのスレッドが終了するのを待機
    for thread in threads:
        thread.join()
    
    results = {key: results[key] for key in sorted(results)}
    return results, is_terminated

def format_solutions(variables, results):
    # 解をフォーマット
    sorted_results = [
        f"{var} = {results[str(var)]}" if not isinstance(results[str(var)], list) 
        else "\n".join(f"{var} = {sol}" for sol in results[str(var)])
        for var in sorted(variables, key=str)
    ]
    result_str =  str("\n".join(sorted_results) or "解なし").replace('**', '^').replace('*', '')
    return result_str

def solve_equation(eq, var, results):
    # 方程式を解いて結果を格納
    try:
        solution = sp.solve(eq, var)
        results[str(var)] = solution
    except Exception as e:
        print(f"解を求める際にエラーが発生しました: {e}")
        results[str(var)] = "解なし"
