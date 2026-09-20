# v0.6.1 ソースコード遮蔽監査（著者確認用）

判定日：2026-09-20。対象は公開済み SIM v0.6 の中心主張。比較対象の SIEL Research Agent は commit `9a914b253cfc650f4065a1a30dc5e8f18dc4e53e` に固定した。監査者は結論文の `PASS` 表記を根拠にせず、各 `evaluate.py` / `verify.py` の入力、演算、`assert`、返却値を読んだ。一次ステータスは **Theoretical derivation**、限定条件は「有限代数について部分的な実計算あり、連続・物理ブリッジは未検証」。この作業は静的コード監査であり、新規の E0/E1/E2 認証、独立再実行、査読ではない。

| 対象 | コードが実際に確認すること | 報告文だけでは成立しないこと | v0.6.1 判定 |
|---|---|---|---|
| BGCE138, 139（CGR） | BGCE138 はスペクトル標識、625 子セル、平坦背景 `3 I_4, Γ=0` 近傍の可逆な滑らか場の存在を構成する。BGCE139 は実際の25事象更新と Yang–Baxter 関係を有限行列で検査する。 | 実際の有限 Braid コフレーム・接続の列が、同じ滑らかな場へ一様な差分境界と共通対数枝を保って収束し、その作用と第1変分まで収束すること。BGCE139 の `formal_CGR_independent_principle_retired=True` は後者の `assert` ではない。 | 有限事象代数は支持。formal CGR 全体の「退役PASS」は撤回。 |
| BGCE099（連続 Einstein） | UTC を前提とした Palatini 作用・方程式を記述し、射影変換の対称 Ricci 不変性を代数的に検査する。 | UTC が実際の Braid 有限場列で成り立つこと、源由来の連続作用・第1変分・物質 Ward 恒等式。 | 条件付き変分定理を維持。無条件導出とはしない。 |
| BGCE143（MMR1） | 625 分割の正規化、積型 tail の条件付き相互情報量、child-constant 例での粗視化等式を検査する。 | 実際の非定数源生成場での収束、任意の滑らかな座標変換に対する Ward 共変性、既存 UB479 物質模型との一致。 | 選んだ滑らかな cylinder 上の形式的構成。物理的 MMR1 完了とはしない。 |
| BGCE185, 187（読出し） | BGCE185 は8 sector の10個の演算子について、固定イベント基底内の有理数ランク・包含を計算する。 | 全10個の可読な展開係数の出力、BGCE187 の全 tilted-state family を実験的一回測定で準備・読出しできること。BGCE187 に対応する実行検証器はない。 | 有限包含は支持。物理的全 `W(a)` 読出しは未達。 |
| BGCE197（RML / MMR2 / `3/5`） | 元の有限 current で射影等式を計算し、既に選んだ head/link 上で `tr(P)/5=3/5` と逆向き `2/5` を検査する。 | なぜ元の物質作用全体 `W(a)` が head に入るのか、なぜ link 方向と重力 bare 側が選択されるのか、物理的結合係数の決定。`W(a)` はコードでは任意スカラーとして掛けられる。 | RML を仮定した有効作用の恒等式のみ。Braid-only MMR2 解除ではない。 |
| BGCE199, 205, 206（反証経路） | BGCE199 は選んだ局所密度例の4-address one-shot effect で残差を計算し、BGCE206 は鋭いイベント・標識の同時読出し障害を検査する。 | 反例の密度が元の全 `W(a_c)` から生成されること、あらゆる局所化・非鋭い POVM・量子 channel・条件付き経路への普遍的 NO-GO。BGCE205 は解析的提案で専用実行器なし。 | 各指定クラスへの限定 NO-GO。一般不可能性ではない。 |

## 最重要の切れ目

`BGCE138/evaluate.py` の `smooth_completion_gate()` は滑らかな場を *こちらで選んで* `E_edge=∫e` と `U_edge=Pexp∫Γ` へ写す向きである。必要な逆向きは、実際の Braid 由来の有限 `E_m,U_m` から共通の `e,Γ` を取り出すこと。さらに `m` に依存しない可逆性・枝・差分境界、作用と第1変分の誤差評価が要る。存在する off-shell 近傍は重要だが、この逆向きの証明ではない。したがって以前の「formal CGR 退役」を継承しない。

`3/5` についても、`BGCE197/evaluate.py` は頭部の rank-3 射影、同方向 link、重力側 bare 規格化を入力してから `3/5` を返す。その算術は正確であり手動係数フィットではないが、入力構造の source-only 選択を示すものではない。逆向きの `2/5` と head-bare の未排除を本文に残した。

## 直接確認したコード

固定 commit `9a914b253cfc650f4065a1a30dc5e8f18dc4e53e` の主な評価器：

- [BGCE138 `evaluate.py`：`smooth_completion_gate()`](https://github.com/SIEL-Research/SIEL-Research-Agent/blob/9a914b253cfc650f4065a1a30dc5e8f18dc4e53e/audits/SRA_DPA_BGCE138_SOURCE_CYLINDER_DIAGONAL_LOCALIZATION_AND_MINIMAL_SMOOTH_CARTAN_COMPLETION_GATE_20260919/evaluate.py#L227-L280)
- [BGCE139 `evaluate.py`：25事象と退役フラグ](https://github.com/SIEL-Research/SIEL-Research-Agent/blob/9a914b253cfc650f4065a1a30dc5e8f18dc4e53e/audits/SRA_DPA_BGCE139_SOURCE_SPECTRAL_CYLINDER_OPERATIONAL_EVENT_IDENTIFICATION_GATE_20260919/evaluate.py)
- [BGCE099 `evaluate.py`：UTC 前提の Palatini 記述](https://github.com/SIEL-Research/SIEL-Research-Agent/blob/9a914b253cfc650f4065a1a30dc5e8f18dc4e53e/audits/SRA_DPA_BGCE099_CONDITIONAL_CONTINUUM_PALATINI_ACTION_AND_VARIATION_THEOREM_20260919/evaluate.py)
- [BGCE143 `evaluate.py`：625-cell の正規化と child-constant 確認](https://github.com/SIEL-Research/SIEL-Research-Agent/blob/9a914b253cfc650f4065a1a30dc5e8f18dc4e53e/audits/SRA_DPA_BGCE143_EXTENSIVE_LOCAL_G1_INTERACTION_TO_QUANTUM_MARKOV_CYLINDER_ACTION_DENSITY_GATE_20260919/evaluate.py)
- [BGCE185 `evaluate.py`：8 sector・10演算子の包含](https://github.com/SIEL-Research/SIEL-Research-Agent/blob/9a914b253cfc650f4065a1a30dc5e8f18dc4e53e/audits/SRA_DPA_BGCE185_FULL_TEN_METRIC_EVENT_READOUT_GATE_20260920/evaluate.py)
- [BGCE197 `evaluate.py`：RML 投影と `3/5`](https://github.com/SIEL-Research/SIEL-Research-Agent/blob/9a914b253cfc650f4065a1a30dc5e8f18dc4e53e/audits/SRA_DPA_BGCE197_RELATIONAL_MARK_LINK_CONDITIONAL_MMR2_20260920/evaluate.py)
- [BGCE199 `evaluate.py`：局所4-address 反例](https://github.com/SIEL-Research/SIEL-Research-Agent/blob/9a914b253cfc650f4065a1a30dc5e8f18dc4e53e/audits/SRA_DPA_BGCE199_ONE_SHOT_FOUR_RAY_EFFECT_LOCAL_COUPLING_GATE_20260920/evaluate.py)

GitHub の可視性・アクセス権は閲覧者ごとに異なる可能性がある。リンク先が読めない場合、この草稿だけで独立再現可能とは言わない。

## 公開範囲と停止条件

本監査表と原稿/PDFは、著者の2026-09-20の指示によりSIM GitHubリポジトリにv0.6.1として別版公開する。v0.6を上書きしない。これはGitHub上の working correction であり、Zenodo DOI、ジャーナル投稿、独立査読を意味しない。SIEL Research Agent のコード全体は本ディレクトリに複製しないため、アクセス可能性は元リポジトリの設定に依存する。今後、未検証の連続極限を無言で「PASS」に戻してはならない。
