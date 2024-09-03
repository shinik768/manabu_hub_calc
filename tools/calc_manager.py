from tools.calc_tools import (
    change_some_alphabets,
    clean_and_prepare_expression,
    get_variable_range,
    solve_equation_in_threads,
    format_solutions,
    split_result,
)
from tools.plot_manager import plot_graph

import sympy as sp

def simplify_or_solve(expression):
    if "起きて" in expression:
        return "すみません！今起きました！"
    try:
        # 式を前処理して、不要な文字やスペースを調整
        expression = clean_and_prepare_expression(expression)
        parts = [part.strip() for part in expression.split(',')]
        expression = parts[0]

        # 変数の範囲を取得（指定されていれば）
        var1_min, var1_max, var2_min, var2_max, var1_range_is_undecided, var2_range_is_undecided \
            = get_variable_range(parts)
        
        equal_sign_count = expression.count('=')

        if equal_sign_count == 1:  # 方程式の場合
            left_expr, right_expr = map(sp.sympify, expression.split('='))
            variables = list(left_expr.free_symbols.union(right_expr.free_symbols))
            eq = sp.Eq(left_expr - right_expr, 0)

            try:
                # 方程式を変数ごとに解く（スレッドを使用）
                solutions, is_terminated = solve_equation_in_threads(eq, variables)
                solution_str = format_solutions(variables, solutions)
                if is_terminated or solution_str[0] == '\n' or '\n\n' in solution_str:
                    if solution_str[0] == '\n':
                        solution_str = solution_str[1:]
                    solution_str.replace('\n\n', '\n')
                    solution_str = f"{solution_str}\n解が存在しないか、計算に時間がかかりすぎるため、一部または全部の解を求められませんでした。申し訳ございません。"

                if len(variables) == 2:  # 変数が2つの場合、グラフを描画
                    var1, var2 = sorted(variables, key=str)
                    intercept_str, image_path = plot_graph(
                        left_expr, right_expr, solutions, str(var1), str(var2),
                        x_min=var1_min, x_max=var1_max, y_min=var2_min, y_max=var2_max,
                        x_range_is_undecided=var1_range_is_undecided,
                        y_range_is_undecided=var2_range_is_undecided
                    )

                    intercepts_str = change_some_alphabets(intercept_str)
                    solutions_str = change_some_alphabets(solution_str)

                    results_str = split_result(solutions_str) + split_result(intercepts_str)
                    
                    if image_path.endswith('.png'):
                        return results_str, image_path
                    else:
                        return results_str + [image_path]
                
                return change_some_alphabets(solution_str)  # 変数が2つでない場合、解を返す
            
            except Exception as e:
                print(f"エラー: {e}")
                return "解を求める際にエラーが発生しました。申し訳ございません。"  # 予期しないエラーのハンドリング

        if equal_sign_count > 1:  # 等号が2つ以上ある場合
            return "方程式には等号 (=) をちょうど1個含めてください！"
        
        # 方程式でない場合、式を簡略化して返す
        simplified_expr = sp.simplify(sp.expand(sp.sympify(expression)))
        return change_some_alphabets(str(simplified_expr).replace('**', '^').replace('*', ''))

    except (sp.SympifyError, TypeError) as e:
        print (expression)
        print(f"SymPy error: {e}")
        return "数式を正しく入力してください！"  # 入力エラー時のメッセージ
