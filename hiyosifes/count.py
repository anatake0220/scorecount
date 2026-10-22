
import os

from flask import Flask, render_template, request, jsonify
from supabase import create_client

app = Flask(__name__)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
delete_password = os.environ.get("RANKING_DELETE_PASSWORD")

if not supabase_url or not supabase_key:
    raise RuntimeError("SUPABASE_URL または SUPABASE_KEY が設定されていません")

supabase = create_client(supabase_url, supabase_key)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit_score", methods=["POST"])
def submit_score():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    score = data.get("score")

    if not name or len(name) > 30:
        return jsonify({
            "error": "名前は1〜30文字で入力してください"
        }), 400

    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        return jsonify({
            "error": "得点が正しくありません"
        }), 400

    try:
        supabase.table("rankings").insert({
            "player_name": name,
            "score": score
        }).execute()

        return jsonify({
            "message": "ランキングに登録しました"
        })

    except Exception:
        app.logger.exception("ランキング登録に失敗しました")
        return jsonify({
            "error": "登録に失敗しました。時間をおいて再度お試しください"
        }), 500


@app.route("/ranking")
def ranking():
    try:
        result = (
            supabase.table("rankings")
            .select("player_name, score, created_at")
            .order("score", desc=True)
            .order("created_at", desc=False)
            .limit(10)
            .execute()
        )

        rankings = result.data or []

        return render_template(
            "ranking.html",
            rankings=rankings
        )

    except Exception:
        app.logger.exception("ランキング取得に失敗しました")
        return (
            "ランキングを読み込めませんでした。"
            "時間をおいて再度お試しください。",
            500
        )


@app.route("/delete_rankings", methods=["POST"])
def delete_rankings():
    if not delete_password:
        app.logger.error("RANKING_DELETE_PASSWORD が設定されていません")
        return jsonify({
            "error": "削除機能の設定が完了していません"
        }), 500

    data = request.get_json(silent=True) or {}
    password = data.get("password", "")

    if not isinstance(password, str) or password != delete_password:
        return jsonify({
            "error": "管理パスワードが違います"
        }), 403

    try:
        supabase.table("rankings").delete().gte("id", 1).execute()

        return jsonify({
            "message": "ランキングを削除しました"
        })

    except Exception:
        app.logger.exception("ランキング削除に失敗しました")
        return jsonify({
            "error": "削除に失敗しました。時間をおいて再度お試しください"
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
