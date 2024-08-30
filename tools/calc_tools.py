import sympy as sp
import re

def clean_expression(expression):
    # アルファベット、数字、特定の記号を許容
    cleaned_expression = re.sub(r'[^a-zA-Z0-9=()!$+*-/*^]', '', expression)
    return cleaned_expression

def change_I_and_i(expression):
    expression = str(expression).replace('i', '<')
    expression = str(expression).replace('I', '>')
    expression = str(expression).replace('<', 'I')
    expression = str(expression).replace('>', 'i')
    return expression

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
        # 変数がある場合のみ多項式を作成
        if term.free_symbols:
            return (sp.Poly(term, *variables).total_degree(), term.as_coefficients_dict().keys())
        else:
            return (0, term.as_coefficients_dict().keys())  # 定数項の場合

    # キーに基づいて項をソート
    sorted_terms = sorted(terms, key=get_sort_key)
    
    # ソートされた項を加算して新しい式を作成
    sorted_expr = sp.Add(*sorted_terms)
    return sorted_expr

def format_expression(expression):
    expanded_expr = sp.expand(sp.sympify(expression))  # 展開
    simplified_expr = sp.simplify(expanded_expr)  # 簡略化
    sorted_expr = sort_expression(simplified_expr)
    formatted_expr = str(sorted_expr).replace('**', '^').replace('*', '')
    return formatted_expr

def format_equation(left_expr, right_expr):
    left_minus_right_expr = sp.simplify(left_expr - right_expr)  # 左辺と右辺の差を簡略化
    formatted_expr = format_expression(left_minus_right_expr)
    return f"{formatted_expr} = 0"