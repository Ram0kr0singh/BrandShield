import React, { useState } from "react";
import { Activity, Note } from "../../api";
import { Clock, MessageSquare, Send } from "lucide-react";

interface ActivityTimelineProps {
  activity: Activity[];
  notes: Note[];
  onAddNote: (content: string) => void;
  busy?: boolean;
}

export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({
  activity,
  notes,
  onAddNote,
  busy = false,
}) => {
  const [newNote, setNewNote] = useState("");

  const handleSubmitNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    onAddNote(newNote.trim());
    setNewNote("");
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      {/* Analyst Notes Section */}
      <div className="aegis-card flex flex-col justify-between">
        <div>
          <span className="font-mono text-[11px] tracking-widest text-[var(--text-muted)] uppercase font-semibold mb-3 block">
            ANALYST INVESTIGATION NOTES
          </span>

          <form onSubmit={handleSubmitNote} className="mb-4">
            <textarea
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="Record forensic observation note..."
              rows={3}
              maxLength={4000}
              className="w-full text-xs font-mono mb-2"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                className="btn btn-accent text-xs"
                disabled={busy || !newNote.trim()}
              >
                <Send size={12} /> Add Analyst Note
              </button>
            </div>
          </form>

          <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
            {notes.length > 0 ? (
              notes.map((n) => (
                <div
                  key={n.id}
                  className="p-3 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded text-xs font-mono"
                >
                  <p className="text-[var(--text-primary)] mb-1">{n.content}</p>
                  <div className="flex items-center gap-2 text-[10px] text-[var(--text-muted)]">
                    <MessageSquare size={10} />
                    <span>{new Date(n.created_at).toLocaleString()}</span>
                    <span>· {n.actor}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs font-mono text-[var(--text-muted)] p-4 text-center">
                No investigation notes added yet.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Forensic Audit Trail Timeline */}
      <div className="aegis-card">
        <span className="font-mono text-[11px] tracking-widest text-[var(--text-muted)] uppercase font-semibold mb-3 block">
          FORENSIC AUDIT TRAIL TIMELINE
        </span>

        <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
          {activity.length > 0 ? (
            activity.map((act) => (
              <div
                key={act.id}
                className="p-3 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded text-xs font-mono"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-[var(--text-primary)] uppercase">
                    {act.event_type.replaceAll("_", " ")}
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)]">
                    {new Date(act.created_at).toLocaleTimeString()}
                  </span>
                </div>
                {act.previous_value || act.new_value ? (
                  <p className="text-[var(--text-secondary)]">
                    {act.previous_value && `${act.previous_value} → `}
                    <span className="text-[var(--color-legitimate)]">{act.new_value}</span>
                  </p>
                ) : null}
                <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)] mt-1">
                  <Clock size={10} />
                  <span>Actor: {act.actor}</span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-xs font-mono text-[var(--text-muted)] p-4 text-center">
              No audit trail records yet.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
