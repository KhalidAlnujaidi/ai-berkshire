import { redirect } from "next/navigation";

// Root page — redirect to default Arabic locale
export default function RootPage() {
  redirect("/ar");
}
