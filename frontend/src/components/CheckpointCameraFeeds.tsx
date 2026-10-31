import type { TrafficCamera } from "../api/schema";

/** Camera metadata for a checkpoint feed slot. */
interface CheckpointCamera {
  id: string;
  label: string;
}

const CHECKPOINT_CAMERAS: CheckpointCamera[] = [
  { id: "2701", label: "Causeway" },
  { id: "4713", label: "Second Link" },
];

/** Props for the fixed checkpoint camera gallery. */
interface CheckpointCameraFeedsProps {
  cameras: TrafficCamera[];
}

function formatCapturedAt(capturedAt?: string): string | undefined {
  if (!capturedAt) return undefined;
  const capturedDate = new Date(capturedAt);
  return Number.isNaN(capturedDate.getTime())
    ? undefined
    : capturedDate.toLocaleString();
}

/** Renders checkpoint camera feeds, including unavailable slots. */
export function CheckpointCameraFeeds({
  cameras,
}: CheckpointCameraFeedsProps) {
  const camerasById = new Map(cameras.map((camera) => [camera.id, camera]));

  return (
    <div className="checkpoint-camera-grid">
      {CHECKPOINT_CAMERAS.map((checkpoint) => {
        const camera = camerasById.get(checkpoint.id);
        const capturedAt = formatCapturedAt(camera?.captured_at);

        return (
          <article className="checkpoint-camera-card" key={checkpoint.id}>
            {camera?.image_url ? (
              <img
                src={camera.image_url}
                alt={`Traffic camera view at ${checkpoint.label}`}
                loading="lazy"
              />
            ) : (
              <p className="checkpoint-camera-unavailable">
                Image not available
              </p>
            )}
            <div>
              <strong>{checkpoint.label}</strong>
              {capturedAt ? (
                <time dateTime={camera?.captured_at}>{capturedAt}</time>
              ) : (
                <small>Timestamp unavailable</small>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}
