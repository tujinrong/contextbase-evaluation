       >>SOURCE FORMAT FREE
identification division.
program-id. STMLOOK.
data division.
working-storage section.
copy "ST-APP.cpy".
procedure division.
    DISPLAY '<option value="1">2026 / 00 / C-A / Fixture</option>'
      WITH NO ADVANCING
    GOBACK.
end program STMLOOK.
