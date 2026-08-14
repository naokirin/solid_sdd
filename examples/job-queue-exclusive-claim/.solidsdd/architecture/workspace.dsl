workspace "Job Queue Exclusive Claim" "Architecture Model for the job-queue-exclusive-claim sample: submission, exclusive claim, and result recording." {
  model {
    job_queue = softwareSystem "JobQueue" "ジョブの投入を受け付け、未クレームジョブのペイロードと存在を保持する。" {
      tags "change:establish-job-queue"
      properties {
        "owns" "Job"
        "public" "SubmitJob"
      }
      claim_coordinator = container "ClaimCoordinator" "同一ジョブへの並行クレーム試行を直列化し、ちょうど1件だけを成功させる。クレーム状態を所有する。" {
        tags "change:establish-job-queue"
        properties {
          "owns" "ClaimState"
          "public" "ClaimJob"
        }
      }
    }
    worker_pool = softwareSystem "WorkerPool" "並行して稼働する複数ワーカーを表し、ジョブのクレームを試み、処理結果を記録する。" {
      tags "change:establish-job-queue"
    }
    result_store = softwareSystem "ResultStore" "完了したジョブの結果を記録し、ジョブIDで取得可能にする。" {
      tags "change:establish-job-queue"
      properties {
        "owns" "JobResult"
        "public" "RecordResult, GetResult"
      }
    }
    worker_pool -> claim_coordinator "ワーカーがジョブのクレームを試みる。並行クレームに対してちょうど1件だけが成功する。" "runtime" {
      tags "change:establish-job-queue, kind:runtime"
    }
    worker_pool -> result_store "処理完了後、結果をジョブIDで記録する。" "runtime" {
      tags "change:establish-job-queue, kind:runtime"
    }
  }
  views {
    systemContext job_queue {
      include *
      autoLayout
    }
    container job_queue {
      include *
      autoLayout
    }
  }
}
