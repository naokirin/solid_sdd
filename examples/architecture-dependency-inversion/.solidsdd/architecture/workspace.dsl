workspace "Architecture Dependency Inversion" "Minimal Architecture Model illustrating dependency inversion (Domain -> Infrastructure becoming Domain -> Port <- Infrastructure)." {
  model {
    inventory = softwareSystem "Inventory" "Own available stock per SKU; expose stock read/adjust operations." {
      tags "change:establish-inventory-persistence, Domain"
      properties {
        "owns" "Stock"
        "public" "InventoryService"
      }
      inventory_repository_port = container "InventoryRepositoryPort" "Persistence abstraction that Inventory depends on and infrastructure adapters implement." "Interface" {
        tags "change:invert-inventory-persistence-dependency, Public"
      }
    }
    postgres_store = softwareSystem "PostgresInventoryStore" "Concrete PostgreSQL persistence for inventory rows." {
      tags "change:establish-inventory-persistence, Infrastructure"
    }
    inventory -> inventory_repository_port "Reads and writes stock through the persistence port." "interface" {
      tags "change:invert-inventory-persistence-dependency, kind:runtime"
    }
    postgres_store -> inventory_repository_port "Implements the persistence port with PostgreSQL." "sql" {
      tags "change:invert-inventory-persistence-dependency, kind:data"
    }
  }
}
