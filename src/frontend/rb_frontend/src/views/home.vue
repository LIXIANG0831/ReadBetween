<template>
  <div class="image-container">
    <div class="search-input">
      <el-input
        v-model="searchVal"
        style="width: 800px"
        :placeholder="t('button.searchPlaceholder')"
        class="input-with-search"
        @keyup.enter="getBQB"
      >
        <template #append>
          <el-button @click="getBQB">{{ t('button.search') }}</el-button>
        </template>
      </el-input>
    </div>

    <LoginDialog />

    <ul v-infinite-scroll="load" :infinite-scroll-disabled="disabled" class="infinite-list">
      <li v-for="(item, index) in countList" :key="index" class="infinite-list-item">
        <el-card>
          <el-image
            :src="item.url"
            :zoom-rate="1.2"
            :max-scale="7"
            :min-scale="0.2"
            :preview-src-list="[item.url]"
            :initial-index="0"
            fit="contain"
          />
          <div class="icon-box">
            <el-icon color="red" @click="likeBQB(item)">
              <IconBxsLike />
            </el-icon>
            <p>{{ item.likes }}</p>
            <el-icon color="#409eff" @click="dislikeBQB(item)">
              <IconBxsDislike />
            </el-icon>
            <p>{{ item.dislikes }}</p>
          </div>
        </el-card>
      </li>
    </ul>
    <el-pagination
      v-model:current-page="currentPage"
      :page-size="size"
      :pager-count="11"
      layout="prev, pager, next"
      :total="total"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import IconBxsLike from '~icons/bxs/like';
import IconBxsDislike from '~icons/bxs/dislike';
import { bqbDislikes, bqbLikes, bqbList } from '@/api/bqb';
import { ElMessage } from 'element-plus';

const { t } = useI18n();
const size = ref(10);
const count = ref(0);
const total = ref(1);
const currentPage = ref(1);
const countList = ref([]);
const loading = ref(false);
const noMore = computed(() => count.value >= 100);
const disabled = computed(() => loading.value || noMore.value);
const searchVal = ref();
const load = () => {
  loading.value = true;
  setTimeout(() => {
    loading.value = false;
  }, 500);
};

function getBQB() {
  bqbList({
    name: searchVal.value,
    page: currentPage.value,
    size: size.value,
  }).then((res) => {
    countList.value = [];
    res.data.data.forEach((element: string) => {
      countList.value.push(element);
    });
    total.value = res.data.total;
  });
}

function likeBQB(item) {
  bqbLikes({ key: item.key }).then((res) => {
    ElMessage.success(res.msg);
    item.likes++;
  });
}

function dislikeBQB(item) {
  bqbDislikes({ key: item.key }).then((res) => {
    ElMessage.success(res.msg);
    item.dislikes++;
  });
}

const handleCurrentChange = (val) => {
  getBQB();
};

onMounted(() => {
  getBQB();
});
</script>

<style lang="scss" scoped>
.image-container {
  position: relative;
  box-sizing: border-box;
  width: 100%;
  height: 85vh;
  padding-top: 80px;

  .center-text {
    height: 20px;
    margin: 10px 0;
    font-size: 14px;
    text-align: center;

    p {
      padding: 0;
      margin: 0;
    }
  }

  .search-input {
    position: absolute;
    top: 30px;
    left: 50%;
    transform: translateX(-50%);
  }

  .infinite-list {
    display: flex;
    flex-wrap: wrap;
    place-content: flex-start center;
    height: 100%;
    padding: 0;
    margin: 0;
    overflow-y: auto;
    list-style: none;
  }

  .infinite-list-item {
    width: 350px;
    height: 350px;
    margin: 10px;

    .el-card {
      width: 350px;
      height: 100%;
    }

    :deep(.el-card__body) {
      box-sizing: border-box;
      height: 100%;
      padding: 30px 20px 40px;
      text-align: center;

      .el-image {
        height: 100%;
      }

      .icon-box {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin-top: 5px;
        font-size: 15px;

        p {
          margin: 0 10px 0 5px;
        }
      }

      .el-icon {
        font-size: 20px;
        cursor: pointer;
      }
    }
  }

  :deep(.el-pagination) {
    justify-content: center;
  }
}
</style>
