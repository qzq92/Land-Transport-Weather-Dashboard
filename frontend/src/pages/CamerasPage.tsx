import { NavLink } from "react-router-dom";
import { useCameras } from "../api/queries";
import { EmptyState, QueryState } from "../components/QueryState";

/** Traffic camera thumbnails and capture timestamps. */
export default function CamerasPage() {
  const query = useCameras();
  const cameras = query.data?.data.cameras ?? [];

  return (
    <>
      <div className="subnav" aria-label="Transport views">
        <NavLink to="/transport" end>Network</NavLink>
        <NavLink to="/transport/travel-times">Travel times</NavLink>
        <NavLink to="/transport/cameras">Cameras</NavLink>
      </div>
      <QueryState
        loading={query.isPending}
        error={query.error}
        fetching={query.isFetching}
        meta={query.data?.meta}
        onRetry={() => void query.refetch()}
      >
        <div className="page-stack">
          {cameras.length ? (
            <div
              className="camera-grid"
              aria-label={`${cameras.length} live traffic camera feeds`}
            >
              {cameras.map((camera) => (
                <article className="camera-card" key={camera.id}>
                  <img
                    src={camera.image_url}
                    alt={`Traffic camera view at ${camera.name}`}
                    loading="lazy"
                  />
                  <div>
                    <strong>{camera.name}</strong>
                    {camera.captured_at && (
                      <time dateTime={camera.captured_at}>
                        {new Date(camera.captured_at).toLocaleString()}
                      </time>
                    )}
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState>No camera feeds are currently available.</EmptyState>
          )}
        </div>
      </QueryState>
    </>
  );
}
