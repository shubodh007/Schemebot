import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export const registerSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Must contain an uppercase letter")
    .regex(/[a-z]/, "Must contain a lowercase letter")
    .regex(/\d/, "Must contain a number"),
  full_name: z.string().min(2, "Name must be at least 2 characters").max(255),
});

export const profileSchema = z.object({
  full_name: z.string().min(2).max(255).optional(),
  phone: z.string().regex(/^\+?[1-9]\d{9,14}$/, "Invalid phone number").optional(),
  date_of_birth: z.string().optional(),
  gender: z.enum(["male", "female", "other", "prefer_not_to_say"]).optional(),
  caste_category: z.enum(["general", "obc", "sc", "st", "ews", "other"]).optional(),
  disability_status: z.enum(["none", "visual", "hearing", "locomotor", "intellectual", "multiple"]).optional(),
  disability_percent: z.number().min(0).max(100).optional(),
  annual_income: z.number().min(0).optional(),
  state_code: z.string().length(2).optional(),
  district: z.string().optional(),
  is_farmer: z.boolean().optional(),
  is_bpl: z.boolean().optional(),
  preferred_language: z.enum(["en", "hi", "te"]).optional(),
});

export type LoginForm = z.infer<typeof loginSchema>;
export type RegisterForm = z.infer<typeof registerSchema>;
export type ProfileForm = z.infer<typeof profileSchema>;
