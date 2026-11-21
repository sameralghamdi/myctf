import { Camera, Trash2 } from "lucide-react";
import { useRef, useState, type ChangeEvent } from "react";
import { api, toMessage, uploadFile } from "../../lib/api";
import { cn, focusRing } from "../../lib/cn";
import { squareJpeg } from "../../lib/image";
import { useToast } from "../feedback/Toast";
import { Avatar } from "./Avatar";
import { Button } from "./Button";
import { Spinner } from "./PageLoader";

interface AvatarUploaderProps {
  name: string;
  src?: string | null;
  /** Called after the photo changed (upload or removal). */
  onChange: () => void | Promise<void>;
}

/** Your avatar with a camera overlay: click to pick a photo, which is cropped and uploaded. */
export function AvatarUploader({ name, src, onChange }: AvatarUploaderProps) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  async function onPick(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow picking the same file again
    if (!file) return;
    setBusy(true);
    try {
      const photo = await squareJpeg(file);
      await uploadFile("/api/profile/avatar", "avatar", photo, "avatar.jpg");
      await onChange();
      toast({ tone: "success", title: "Profile photo updated" });
    } catch (caught) {
      toast({ tone: "danger", title: "Couldn't update your photo", description: toMessage(caught) });
    } finally {
      setBusy(false);
    }
  }

  async function onRemove() {
    setBusy(true);
    try {
      await api("/api/profile/avatar", { method: "DELETE" });
      await onChange();
      toast({ tone: "info", title: "Profile photo removed" });
    } catch (caught) {
      toast({ tone: "danger", title: "Couldn't remove your photo", description: toMessage(caught) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-start gap-2">
      <button
        type="button"
        onClick={() => input.current?.click()}
        disabled={busy}
        aria-label={src ? "Change profile photo" : "Upload a profile photo"}
        className={cn("group relative rounded-full ring-4 ring-gray-900", focusRing)}
      >
        <Avatar name={name} src={src} size="xl" />
        <span
          aria-hidden="true"
          className={cn(
            "absolute inset-0 grid place-items-center rounded-full bg-gray-950/60 text-white transition-opacity duration-200",
            busy ? "opacity-100" : "opacity-0 group-hover:opacity-100 group-focus-visible:opacity-100",
          )}
        >
          {busy ? <Spinner /> : <Camera className="h-6 w-6" />}
        </span>
        {!busy && (
          <span aria-hidden="true" className="absolute -bottom-1 -right-1 grid h-8 w-8 place-items-center rounded-full border-2 border-gray-900 bg-brand-600 text-white shadow-md transition-transform duration-200 group-hover:scale-110">
            <Camera className="h-4 w-4" />
          </span>
        )}
      </button>
      <input
        ref={input}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        className="sr-only"
        tabIndex={-1}
        onChange={(event) => void onPick(event)}
      />
      {src && (
        <Button variant="ghost" size="sm" disabled={busy} onClick={() => void onRemove()} className="h-6 px-2 text-xs text-gray-400">
          <Trash2 aria-hidden="true" className="h-3 w-3" />
          Remove photo
        </Button>
      )}
    </div>
  );
}
