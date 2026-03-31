"use client";

import { useState } from "react";
import { nxApi, type NxDeal } from "@/lib/nexus-api";

interface UseEditableFieldOptions {
  dealId: number;
  onSaved: () => void;
}

export function useEditableField({ dealId, onSaved }: UseEditableFieldOptions) {
  const [editField, setEditField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState(false);

  const startEdit = (field: string, currentValue: string) => {
    setEditField(field);
    setEditValue(currentValue || "");
  };

  const cancelEdit = () => {
    setEditField(null);
    setEditValue("");
  };

  const saveField = async () => {
    if (!editField) return;
    setSaving(true);
    try {
      let value: string | number | null = editValue;
      if (editField === "budget_amount") {
        const n = parseFloat(editValue);
        value = isNaN(n) ? null : n;
      }
      await nxApi.deals.update(dealId, { [editField]: value } as Partial<NxDeal>);
      cancelEdit();
      onSaved();
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") saveField();
    if (e.key === "Escape") cancelEdit();
  };

  return { editField, editValue, setEditValue, saving, startEdit, cancelEdit, saveField, handleKeyDown };
}
