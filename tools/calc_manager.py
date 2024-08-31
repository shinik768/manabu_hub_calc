from tools.calc_tools import (
    TimeoutException,
    change_I_and_i,
    clean_and_prepare_expression,
    get_variable_range,
    solve_equation_in_threads,
    format_solutions,
)
from tools.plot_manager import plot_graph
import sympy as sp

def simplify_or_solve(expression):
    try:
        # 式を前処理して、不要な文字やスペースを調整
        expression = clean_and_prepare_expression(expression)
        parts = [part.strip() for part in expression.split(',')]
        expression = parts[0]

        # 変数の範囲を取得（指定されていれば）
        var1_min, var1_max = get_variable_range(parts)
        equal_sign_count = expression.count('=')

        if equal_sign_count == 1:  # 方程式の場合
            left_expr, right_expr = map(sp.sympify, expression.split('='))
            variables = list(left_expr.free_symbols.union(right_expr.free_symbols))
            eq = sp.Eq(left_expr - right_expr, 0)

            try:
                # 方程式を変数ごとに解く（スレッドを使用）
                results = solve_equation_in_threads(eq, variables)
                result_str = format_solutions(variables, results)

                if len(variables) == 2:  # 変数が2つの場合、グラフを描画
                    var1, var2 = sorted(variables, key=str)
                    image_path = plot_graph(left_expr, right_expr, str(var1), str(var2), x_min=var1_min, x_max=var1_max)
                    if image_path != f"{var1_min}<={var1}<={var1_max}の範囲内ではグラフを描画できません。":
                        return result_str, image_path
                    else:
                        return result_str + "\n" + image_path

                return change_I_and_i(result_str)  # 変数が2つでない場合、解を返す
            
            except TimeoutException:
                return "解を求めるのに時間がかかりすぎました。"  # タイムアウト時のメッセージ
            except Exception as e:
                print(f"エラー: {e}")
                return "解を求める際にエラーが発生しました。"  # 予期しないエラーのハンドリング

        if equal_sign_count > 1:  # 等号が2つ以上ある場合
            return "方程式には等号 (=) をちょうど1個含めてください！"
        
        # 方程式でない場合、式を簡略化して返す
        simplified_expr = sp.simplify(sp.expand(sp.sympify(expression)))
        return change_I_and_i(str(simplified_expr).replace('**', '^').replace('*', ''))

    except (sp.SympifyError, TypeError) as e:
        print (expression)
        print(f"SymPy error: {e}")
        return "数式を正しく入力してください！"  # 入力エラー時のメッセージ
