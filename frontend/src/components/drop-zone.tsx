"use client";

import { useState, useCallback, type ReactNode, type DragEvent } from "react";
import { Upload } from "lucide-react";

interface DropZoneProps {
  children: ReactNode;
  onFilesDropped: (files: File[]) => void;
  disabled?: boolean;
}

export function DropZone({ children, onFilesDropped, disabled }: DropZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [dragCounter, setDragCounter] = useState(0);

  const handleDragEnter = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (disabled) return;
      setDragCounter((c) => c + 1);
      if (e.dataTransfer.types.includes("Files")) {
        setDragging(true);
      }
    },
    [disabled],
  );

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter((c) => {
      const next = c - 1;
      if (next <= 0) setDragging(false);
      return Math.max(0, next);
    });
  }, []);

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const extractFiles = useCallback(async (items: DataTransferItemList): Promise<File[]> => {
    const files: File[] = [];
    const entries: FileSystemEntry[] = [];

    for (let i = 0; i < items.length; i++) {
      const entry = items[i].webkitGetAsEntry?.();
      if (entry) entries.push(entry);
    }

    const readEntry = (entry: FileSystemEntry): Promise<File[]> =>
      new Promise((resolve) => {
        if (entry.isFile) {
          (entry as FileSystemFileEntry).file(
            (f) => resolve([f]),
            () => resolve([]),
          );
        } else if (entry.isDirectory) {
          const reader = (entry as FileSystemDirectoryEntry).createReader();
          reader.readEntries(
            async (subEntries) => {
              const nested = await Promise.all(subEntries.map(readEntry));
              resolve(nested.flat());
            },
            () => resolve([]),
          );
        } else {
          resolve([]);
        }
      });

    for (const entry of entries) {
      const result = await readEntry(entry);
      files.push(...result);
    }

    return files;
  }, []);

  const handleDrop = useCallback(
    async (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragging(false);
      setDragCounter(0);
      if (disabled) return;

      let files: File[];
      if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
        files = await extractFiles(e.dataTransfer.items);
      } else {
        files = Array.from(e.dataTransfer.files);
      }

      if (files.length > 0) {
        onFilesDropped(files);
      }
    },
    [disabled, extractFiles, onFilesDropped],
  );

  return (
    <div
      className="relative h-full"
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {children}
      {dragging && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-blue-500/10 backdrop-blur-sm border-2 border-dashed border-blue-500 rounded-xl pointer-events-none">
          <div className="flex flex-col items-center gap-2 text-blue-500">
            <Upload size={40} />
            <p className="text-lg font-semibold">拖放檔案到此處</p>
            <p className="text-sm opacity-70">支援 PDF, PPT, PPTX, DOCX</p>
          </div>
        </div>
      )}
    </div>
  );
}
