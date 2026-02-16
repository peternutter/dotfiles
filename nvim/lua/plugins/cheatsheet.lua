return {
  {
    "bjarneo/lazyvim-cheatsheet.nvim",
    keys = {
      {
        "ch",
        function()
          require("lazyvim-cheatsheet").show()
        end,
        desc = "Show LazyVim Cheatsheet",
      },
    },
  },
}
