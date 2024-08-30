from tools.calc_tools import (
    clean_expression,
    change_I_and_i,
    add_spaces,
    add_multiplication_sign,
    add_exponentiation_sign,
)

from tools.plot_tool import plot_graph
import sympy as sp
import threading

class TimeoutException(Exception):
    pass

def solve_equation(eq, var, result_container):
    result_container.append(sp.solve(eq, var))

def simplify_or_solve(expression):
    try:
        # カンマで区切って部分を取得
        expression = clean_expression(expression)
        parts = [part.strip() for part in expression.split(',')]
        expression = parts[0]

        # グラフ表示用のxの最小値、最大値をあらかじめ指定
        var1_min = -5
        var1_max = 5

        if (len(parts) == 3):
            try:
                num1 = float(parts[1])
                num2 = float(parts[2])
                var1_min = min(num1, num2)
                var1_max = max(num1, num2)
            except Exception as e:
                print(e)
                pass

        expression = add_spaces(expression)
        expression = change_I_and_i(expression)
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

            try:
                # 結果を格納するためのリスト
                results = []
                threads = []

                # 変数ごとにスレッドを作成
                for var in variables:
                    thread = threading.Thread(target=solve_equation, args=(eq, var, results))
                    threads.append(thread)
                    thread.start()

                # スレッドの完了を待つ
                for thread in threads:
                    thread.join(timeout=10)  # 10秒待機
                    if thread.is_alive():  # スレッドがまだ動いている場合
                        print("解を求めるのに時間がかかりすぎました。")
                        raise TimeoutException("解を求めるのに時間がかかりすぎました。")

                # 解の表示形式を調整
                result = ""
                sorted_results = []

                for var in sorted(variables, key=lambda v: str(v)):  # アルファベット順でソート
                    index = variables.index(var)
                    sols = results[index]
                    if isinstance(sols, list):
                        for sol in sols:
                            sorted_results.append(f"{var} = {sol}")
                    else:
                        sorted_results.append(f"{var} = {sols}")

                result_str = "\n".join(sorted_results).strip() if sorted_results else "解なし"  # 解がない場合の処理
                result_str = str(result_str).replace('**', '^').replace('*', '')  # 形式を整形
                result_str = change_I_and_i(result_str)

            except TimeoutException as e:
                print("解を求めるのに時間がかかりすぎました。")
                result_str = "解を求めるのに時間がかかりすぎました。"
            except Exception as e:
                print(f"エラー: {e}")
                result_str = "解を求める際にエラーが発生しました。"
            print(len(variables))
            if len (variables) != 2:
                    return result_str
            else:
                var1, var2 = sorted(variables, key=lambda v: str(v))  # アルファベット順でソート
                image_path = plot_graph(left_expr, right_expr, str(var1), str(var2), x_min=var1_min, x_max=var1_max)  # グラフを描画
                if image_path == f"{var1_min}<={var1}<={var1_max}の範囲内ではグラフを描画できません。":
                    return result_str + "\n" + image_path
                else:
                    return result_str, image_path

        elif equal_sign_count > 1:
            return "方程式には等号 (=) をちょうど1個含めてください！"
        else:
            expanded_expr = sp.expand(sp.sympify(expression))  # 展開
            simplified_expr = sp.simplify(expanded_expr)  # 簡略化
            simplified_expr_str = str(simplified_expr).replace('**', '^').replace('*', '')  # 形式を整形
            result_str = change_I_and_i(simplified_expr_str)

            return f"{result_str}"

    except (sp.SympifyError, TypeError) as e:
        print(f"SymPy error: {e}")
        return "数式を正しく入力してください！"