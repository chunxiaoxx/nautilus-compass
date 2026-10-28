import { z } from 'zod'

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, '邮箱不能为空')
    .email('请输入有效的邮箱地址'),
  password: z
    .string()
    .min(1, '密码不能为空')
    .min(8, '密码至少需要8个字符'),
  rememberMe: z.boolean().optional(),
})

export const registerSchema = z
  .object({
    email: z
      .string()
      .min(1, '邮箱不能为空')
      .email('请输入有效的邮箱地址'),
    password: z
      .string()
      .min(1, '密码不能为空')
      .min(12, '密码至少需要12个字符')
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])/,
        '密码必须包含大小写字母、数字和特殊字符'
      ),
    confirmPassword: z.string().min(1, '请确认密码'),
    acceptTerms: z
      .boolean()
      .refine((val) => val === true, '请同意用户协议'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: '两次输入的密码不一致',
    path: ['confirmPassword'],
  })

export const walletLoginSchema = z.object({
  walletAddress: z
    .string()
    .min(1, '钱包地址不能为空')
    .regex(/^0x[a-fA-F0-9]{40}$/, '无效的钱包地址'),
  signature: z.string().min(1, '签名不能为空'),
})

export type LoginFormData = z.infer<typeof loginSchema>
export type RegisterFormData = z.infer<typeof registerSchema>
export type WalletLoginFormData = z.infer<typeof walletLoginSchema>
