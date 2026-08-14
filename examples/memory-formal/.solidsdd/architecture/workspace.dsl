workspace "Exclusive Memory" "Architecture Model connecting state ownership to the ExclusiveMemory TLA+ concurrency sample." {
  model {
    memory_register = softwareSystem "MemoryRegister" "Own the shared memory register and its exclusive-ownership acquire/add/release protocol." {
      tags "change:establish-exclusive-memory-architecture"
      properties {
        "owns" "Mem"
        "public" "AcquireOwnership, AddAndRelease"
      }
    }
    client = softwareSystem "Client" "Acquire ownership of the register, add once, then release." {
      tags "change:establish-exclusive-memory-architecture"
    }
    client -> memory_register "Acquires ownership, mutates mem, releases." "runtime" {
      tags "change:establish-exclusive-memory-architecture, kind:runtime"
    }
  }
  views {
    systemContext memory_register {
      include *
      autoLayout
    }
  }
}
