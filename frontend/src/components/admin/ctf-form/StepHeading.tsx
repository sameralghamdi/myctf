interface StepHeadingProps {
  title: string;
  description: string;
}

/** Title + one-line explanation at the top of every step. */
export function StepHeading({ title, description }: StepHeadingProps) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-lg font-semibold text-gray-50">{title}</h2>
      <p className="max-w-2xl text-sm text-gray-400">{description}</p>
    </div>
  );
}
