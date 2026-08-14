workspace "Inventory Reservation" "Architecture Model for the inventory-reservation sample" {
  model {
    inventory = softwareSystem "Inventory" "Own available stock per SKU; expose stock read/adjust operations." {
      tags "change:structure-inventory-reservation-split"
      properties {
        "owns" "Stock"
        "public" "InventoryService"
      }
    }
    reservation = softwareSystem "Reservation" "Own hold lifecycle (reserve/release/expire/lookup) and TTL/authZ enforcement." {
      tags "change:structure-inventory-reservation-split"
      properties {
        "owns" "Hold"
        "public" "ReservationService"
      }
    }
    reservation -> inventory "Reserving and releasing a hold must read and adjust available stock." "runtime" {
      tags "change:structure-inventory-reservation-split, kind:runtime"
    }
    notification = softwareSystem "Notification" "Own hold-expiry notification delivery (channel, formatting, retry)." {
      tags "change:add-notification-module"
      properties {
        "owns" "NotificationLog"
        "public" "NotificationService"
      }
    }
    notification -> reservation "Reads hold-expiry events to notify the holder." "event" {
      tags "change:add-notification-module, kind:event"
    }
  }
  views {
    systemContext inventory {
      include *
      autoLayout
    }
  }
}
