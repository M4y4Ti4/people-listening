live_loop :listener do
  note = sync "/osc*/play_note"
  note_value = note[0]
  play note_value, attack: 0, release: 0.5
  puts "Played: #{note_value}"
end