"use client";

import { mediaAbsolute, type GenerationJob } from "@/lib/api";

export function MediaPreview({ job }: { job: GenerationJob }) {
  const media = mediaAbsolute(job.media_url);
  const audio = mediaAbsolute(job.audio_url);

  if (!media) {
    return <p className="text-sm text-[var(--mist)]">No preview yet.</p>;
  }

  if (job.modality === "video") {
    return (
      <div className="space-y-3">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={media}
          alt={job.prompt ?? "Video proxy"}
          className="w-full border border-[var(--line)] bg-black object-cover aspect-video"
        />
        {audio ? (
          <audio controls src={audio} className="w-full">
            Your browser does not support audio.
          </audio>
        ) : null}
      </div>
    );
  }

  if (job.modality === "image") {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={media}
        alt={job.prompt ?? "Image"}
        className="w-full border border-[var(--line)] bg-black object-cover aspect-video"
      />
    );
  }

  return (
    <div className="border border-[var(--line)] bg-[rgba(10,15,22,0.55)] p-4">
      <p className="ac-display mb-3 text-[0.68rem] tracking-[0.2em] text-[var(--mist)] uppercase">
        {job.modality} playback
      </p>
      <audio controls src={media} className="w-full">
        Your browser does not support audio.
      </audio>
    </div>
  );
}
