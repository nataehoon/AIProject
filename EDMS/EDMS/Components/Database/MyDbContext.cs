using EDMS.Components.Models.Entity;
using Microsoft.EntityFrameworkCore;

namespace EDMS.Components.Database
{
    public class MyDbContext : DbContext
    {
        public MyDbContext(DbContextOptions<MyDbContext> options) : base(options) { }

        public DbSet<DocFileInfo> DocFileInfo => Set<DocFileInfo>();
        public DbSet<DocFilePage> DocFilePage => Set<DocFilePage>();

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder
                .UseCollation("utf8mb4_general_ci")
                .HasCharSet("utf8mb4");

            modelBuilder.Entity<DocFileInfo>(entity =>
            {
                entity.ToTable("doc_file_info");

                entity.HasKey(e => e.IDX).HasName("PRIMARY");

                entity.HasIndex(e => e.UID, "in_doc_file_info_UID").IsUnique();
                entity.HasIndex(e => e.Title, "in_doc_file_info_Title");

                entity.Property(e => e.IDX)
                    .HasMaxLength(40)
                    .HasComment("IDX 기본키")
                    .HasColumnName("IDX");
                entity.Property(e => e.UID)
                    .HasMaxLength(40)
                    .HasComment("UID 고유값")
                    .HasColumnName("UID");
                entity.Property(e => e.FileName)
                    .HasMaxLength(500)
                    .HasComment("파일 이름")
                    .HasColumnName("FileName");
                entity.Property(x => x.Title)
                    .HasMaxLength(500)
                    .HasComment("파일 제목")
                    .HasColumnName("Title");
                entity.Property(e => e.MainText)
                    .HasColumnType("text")
                    .HasComment("간략 소개")
                    .HasColumnName("MainText")
                    .IsRequired(false);
                entity.Property(e => e.FileSize)
                    .HasDefaultValueSql("'0'")
                    .HasComment("파일 사이즈")
                    .HasColumnName("FileSize");
                entity.Property(e => e.Registrant)
                    .HasMaxLength(40)
                    .HasComment("등록자 UID")
                    .HasColumnName("Registrant")
                    .IsRequired(false);
                entity.Property(e => e.FilePath)
                    .HasColumnType("text")
                    .HasComment("저장 경로")
                    .HasColumnName("FilePath");
                entity.Property(e => e.Tags)
                    .HasColumnType("text")
                    .HasComment("태그")
                    .HasColumnName("Tags")
                    .IsRequired(false);
                entity.Property(e => e.CreateAt)
                    .HasColumnType("datetime")
                    .HasComment("생성일")
                    .HasColumnName("CreateAt");
                entity.Property(e => e.UpdateAt)
                    .HasColumnType("datetime")
                    .HasComment("수정일")
                    .HasColumnName("UpdateAt");
            });

            modelBuilder.Entity<DocFilePage>(entity =>
            {
                entity.ToTable("doc_file_page");

                entity.HasKey(e => e.IDX).HasName("PRIMARY");

                entity.HasIndex(e => e.UID, "in_doc_page_info_UID").IsUnique();
                entity.HasIndex(e => e.Link_Doc, "in_doc_page_info_Link_Doc");

                entity.Property(e => e.IDX)
                   .HasMaxLength(40)
                   .HasComment("IDX 기본키")
                   .HasColumnName("IDX");
                entity.Property(e => e.UID)
                    .HasMaxLength(40)
                    .HasComment("UID 고유값")
                    .HasColumnName("UID");
                entity.Property(e => e.PageNum)
                    .HasDefaultValueSql("'0'")
                    .HasComment("페이지 넘버")
                    .HasColumnName("PageNum");
                entity.Property(e => e.Content)
                    .HasColumnType("text")
                    .HasComment("내용")
                    .HasColumnName("Content")
                    .IsRequired(false);
                entity.Property(e => e.Link_Doc)
                    .HasMaxLength(40)
                    .HasComment("연결된 문서")
                    .HasColumnName("Link_Doc");
                entity.Property(e => e.CreateAt)
                    .HasColumnType("datetime")
                    .HasComment("생성일")
                    .HasColumnName("CreateAt");
                entity.Property(e => e.UpdateAt)
                    .HasColumnType("datetime")
                    .HasComment("수정일")
                    .HasColumnName("UpdateAt");

                entity.HasOne(d => d.Link_Doc_Navigation).WithMany(p => p.DocFilePage)
                    .HasPrincipalKey(d => d.UID)
                    .HasForeignKey(d => d.Link_Doc)
                    .OnDelete(DeleteBehavior.Cascade)
                    .HasConstraintName("fk_doc_file_page_Link_Doc");
            });

            modelBuilder.Entity<ChatRoom>(entity =>
            {
                entity.ToTable("chat_room");
                entity.HasKey(e => e.IDX).HasName("PRIMARY");
                entity.HasIndex(e => e.UID, "in_chat_room_UID").IsUnique();
                entity.HasIndex(e => e.UserId, "in_chat_UserId");

                entity.Property(e => e.IDX)
                    .HasMaxLength(40)
                    .HasComment("IDX 기본키")
                    .HasColumnName("IDX");
                entity.Property(e => e.UID)
                    .HasMaxLength(40)
                    .HasComment("UID 고유값")
                    .HasColumnName("UID");
                entity.Property(e => e.UserId)
                    .HasMaxLength(40)
                    .HasComment("유저 ID")
                    .HasColumnName("UserId");
                entity.Property(e => e.Title)
                    .HasColumnType("text")
                    .HasComment("채팅룸 제목")
                    .HasColumnName("Title");
            });

            modelBuilder.Entity<Chatting>(entity =>
            {
                entity.ToTable("chatting");
                entity.HasKey(e => e.IDX).HasName("PRIMARY");
                entity.HasIndex(e => e.Link_RoomId, "in_chatting_Link_RoomId");

                entity.Property(e => e.IDX)
                   .HasMaxLength(40)
                   .HasComment("IDX 기본키")
                   .HasColumnName("IDX");
                entity.Property(e => e.UID)
                    .HasMaxLength(40)
                    .HasComment("UID 고유값")
                    .HasColumnName("UID");
                entity.Property(e => e.IsUser)
                    .HasDefaultValueSql("'0'")
                    .HasComment("유저 구분자 0: 시스템, 1:유저")
                    .HasColumnName("IsUser");
                entity.Property(e => e.Content)
                    .HasColumnType("text")
                    .HasComment("채팅 내용")
                    .HasColumnName("Content");
                entity.Property(e => e.CreateAt)
                    .HasColumnType("datetime")
                    .HasComment("생성일")
                    .HasColumnName("CreateAt");
                entity.Property(e => e.Link_RoomId)
                    .HasMaxLength(40)
                    .HasComment("연결된 채팅룸")
                    .HasColumnName("Link_RoomId");

                entity.HasOne(d => d.Link_RoomId_Navigation).WithMany(p => p.Chatting)
                    .HasPrincipalKey(d => d.UID)
                    .HasForeignKey(d => d.Link_RoomId)
                    .OnDelete(DeleteBehavior.Cascade)
                    .HasConstraintName("fk_chatting_Link_RoomId");
            });

            base.OnModelCreating(modelBuilder);
        }
    }
}
