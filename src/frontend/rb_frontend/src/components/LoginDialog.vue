<template>
  <el-dialog v-model="dialogStore.loginDialogVisible" :title="t('login.emailLogin')" width="500">
    <el-form ref="formRef" :model="form" :rules="rules">
      <el-form-item :label="t('login.email')" :placeholder="t('login.emailPlaceholder')" prop="email">
        <el-input v-model="form.email" autocomplete="off" />
      </el-form-item>
      <el-form-item :label="t('login.code')" prop="code">
        <el-input v-model="form.code" autocomplete="off">
          <template #suffix>
            <span>|</span>
            <span ref="spanRef" @click="sendValidationCode(form.email)">
              {{ isSendValidationCode }}
            </span>
          </template>
        </el-input>
      </el-form-item>
      <!-- <el-form-item>
        <el-input :placeholder="t('login.captchaPlaceholder')"
                    v-model="form.captcha"
                    type="tel">
            <template slot="append"><img class="reg_code_img"
                   :src="captchaSrc"
                   @click="captchaUpdata"></template>
          </el-input>
      </el-form-item> -->
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel(formRef)">Cancel</el-button>
        <el-button type="primary" @click="handleConfirm"> Confirm </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue';
import { useDialogStore } from '@/store/dialog';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage } from 'element-plus';
import { isEmail } from '@/utils/format';
import { emailCode, loginEmail } from '@/api/general';
import { setItem } from '@/utils/localStorage';

const { t } = useI18n();
const dialogStore = useDialogStore();
// 验证码区域文字说明
const spanRef = ref();
const isSendValidationCode = ref<string>(t('login.sendEmailCode'));

const formRef = ref<FormInstance>();
const form = reactive({
  email: '',
  code: '',
  // captcha: '',
  remember: false,
});

const validateEmail = (rule: any, value: any, callback: any) => {
  if (isEmail(value)) {
    callback();
  } else {
    callback(new Error(t('login.emailValidate')));
  }
};

const rules = reactive<FormRules<typeof form>>({
  email: [{ validator: validateEmail, trigger: 'blur' }],
});

// 发送验证码
async function sendValidationCode(email: string) {
  // 若显示的发送验证码区域文字 不是 '发送验证码'，就直接返回不再执行
  if (!isSendValidationCode.value.endsWith(t('login.sendEmailCode'))) return;
  await formRef.value!.validateField('email');
  // 重新发送逻辑
  isSendValidationCode.value = `60 ${t('login.emailCodeTimeout')}`;
  spanRef.value.style = 'color: gray;'; // 颜色变灰
  const countDown = ref<number>(60); // 倒计时
  const temp = setInterval(() => {
    countDown.value--;
    isSendValidationCode.value = countDown.value + t('login.emailCodeTimeout');
    if (!countDown.value) {
      clearInterval(temp);
      spanRef.value.style = 'color: #1764FF;'; // 颜色变蓝
      isSendValidationCode.value = t('login.resendCode');
      countDown.value = 60;
    }
  }, 1000);
  // 发送
  try {
    const res = await emailCode({ email: email }); // 返回boolean
    if (res.data) ElMessage.success(t('sendCodeSuccess'));
  } catch {
    ElMessage.error(t('sendCodeFail'));
  }
}

// 提交表单
async function handleConfirm() {
  loginEmail(form).then((res) => {
    console.log(res.data);
    if (res.data.code === 200) {
      setItem('accessToken', res.data.data.access_token);
      setItem('refreshToken', res.data.data.refresh_token);
      setItem('email', form.email);
      dialogStore.closeLoginDialog();
    } else {
      ElMessage.error(res.data.msg);
    }
  });
}
// 取消
async function handleCancel(formEl: FormInstance | undefined) {
  if (!formEl) return;
  formEl.resetFields();
  dialogStore.closeLoginDialog();
}
</script>
