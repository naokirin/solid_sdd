Feature: ジョブキューへの投入と排他的クレーム
  Job Queue はジョブの投入を受け付け、複数のワーカーが並行してクレームを試みても
  各ジョブがちょうど1人のワーカーにのみクレームされることを保証し、完了結果を記録する。
  See .solidsdd/architecture/workspace.dsl for the module that owns each piece of
  state, and formal/ClaimCoordinator.tla for the checked exclusivity property.

  @R1
  Scenario: プロデューサーがジョブを投入する
    Given ジョブキューが空である
    When プロデューサーがペイロードを持つ新しいジョブを投入する
    Then ジョブは未クレーム状態で保存され、ジョブIDが割り当てられる

  @R2 @SC1 @SC2
  Scenario: 複数ワーカーが同一ジョブへ並行してクレームを試みても1人だけが成功する
    Given 未クレームのジョブが1件存在する
    And 2人のワーカーが同時にそのジョブのクレームを試みる
    When 両方のクレームリクエストが並行して処理される
    Then ちょうど1人のワーカーのクレームが成功する
    And もう1人のワーカーは「既にクレーム済み」という結果を受け取る

  @R3
  Scenario: 完了したジョブの結果が記録され取得できる
    Given ワーカーがジョブのクレームに成功し処理を完了している
    When ワーカーが処理結果を記録する
    Then その結果はジョブIDで取得可能になる
