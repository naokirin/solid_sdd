workspace "Fixture" "Architecture DSL forbidden-dependency fixture" {
  model {
    a = softwareSystem "A" "A." {
      tags "change:case1"
    }
    b = softwareSystem "B" "B." {
      tags "change:case1"
    }
    a -> b "a needs b" {
      tags "change:case1"
    }
  }
}
